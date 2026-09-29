"""Password accounts, revocable cookie sessions, and proof of wallet ownership."""
import asyncio
import hashlib
import hmac
import os
import re
import secrets
from urllib.parse import urlparse

import asyncpg
from eth_account import Account
from eth_account.messages import encode_defunct
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel, Field, field_validator
from web3 import Web3
from .pgvector_client import get_conn

ORIGIN = os.getenv("FRONTEND_ORIGIN", "http://localhost:3000").rstrip("/")
SECURE = urlparse(ORIGIN).scheme == "https"
COOKIE = "__Host-dkm_session" if SECURE else "dkm_session"
router = APIRouter(prefix="/api/auth", tags=["Account"])
_hash_slots = asyncio.Semaphore(2)


async def setup_auth():
    conn = await get_conn()
    try:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS app_users (
                id BIGSERIAL PRIMARY KEY, username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL, wallet_address TEXT UNIQUE,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            );
            CREATE TABLE IF NOT EXISTS app_sessions (
                token_hash TEXT PRIMARY KEY, user_id BIGINT NOT NULL REFERENCES app_users(id),
                expires_at TIMESTAMPTZ NOT NULL, wallet_message TEXT,
                challenge_expires TIMESTAMPTZ
            );
            CREATE TABLE IF NOT EXISTS auth_attempts (
                key TEXT PRIMARY KEY, attempts INT NOT NULL, expires_at TIMESTAMPTZ NOT NULL
            );
            ALTER TABLE knowledge_assets ADD COLUMN IF NOT EXISTS user_id BIGINT REFERENCES app_users(id);
            ALTER TABLE payment_orders ADD COLUMN IF NOT EXISTS user_id BIGINT REFERENCES app_users(id);
        """)
    finally:
        await conn.close()


def digest(token):
    return hashlib.sha256(token.encode()).hexdigest()


def password_hash(password, salt=None):
    salt = salt or secrets.token_hex(16)
    key = hashlib.scrypt(password.encode(), salt=bytes.fromhex(salt), n=2**17, r=8, p=1, maxmem=256*1024*1024)
    return salt + ":" + key.hex()


async def hash_password(password, salt=None):
    # ponytail: cap scrypt memory per worker; use a shared admission queue at scale.
    async with _hash_slots:
        return await asyncio.to_thread(password_hash, password, salt)


def same_origin(request: Request):
    # Custom header forces a CORS preflight; exact Origin also rejects sibling sites.
    if request.headers.get("origin") != ORIGIN or request.headers.get("x-dkm-request") != "1":
        raise HTTPException(403, "Request origin is not allowed")


async def current_user(request: Request):
    if request.method not in ("GET", "HEAD", "OPTIONS"):
        same_origin(request)
    conn = await get_conn()
    try:
        row = await conn.fetchrow("""
            SELECT u.id, u.username, u.wallet_address FROM app_users u
            JOIN app_sessions s ON s.user_id=u.id
            WHERE s.token_hash=$1 AND s.expires_at>NOW()
        """, digest(request.cookies.get(COOKIE, "")))
    finally:
        await conn.close()
    if not row:
        raise HTTPException(401, "Please log in to continue")
    return dict(row)


async def wallet_user(user=Depends(current_user)):
    if not user["wallet_address"]:
        raise HTTPException(403, "Verify your wallet in Account first")
    return user


class Credentials(BaseModel):
    username: str = Field(min_length=3, max_length=40)
    password: str = Field(min_length=12, max_length=128)

    @field_validator("username")
    @classmethod
    def normalize(cls, value):
        value = value.strip().lower()
        if not re.fullmatch(r"[a-z0-9_]{3,40}", value):
            raise ValueError("Use 3–40 letters, numbers or underscores")
        return value


async def throttle(request, username):
    conn = await get_conn()
    try:
        await conn.execute("DELETE FROM auth_attempts WHERE expires_at<NOW()")
        for key, limit in [("user:" + username, 10), ("ip:" + (request.client.host if request.client else "unknown"), 50)]:
            count = await conn.fetchval("""
                INSERT INTO auth_attempts VALUES ($1,1,NOW()+INTERVAL '15 minutes')
                ON CONFLICT (key) DO UPDATE SET attempts=auth_attempts.attempts+1
                RETURNING attempts
            """, digest(key))
            if count > limit:
                raise HTTPException(429, "Too many attempts. Try again in 15 minutes.")
    finally:
        await conn.close()


async def new_session(conn, request, response, user_id):
    await conn.execute("DELETE FROM app_sessions WHERE expires_at<NOW() OR token_hash=$1", digest(request.cookies.get(COOKIE, "")))
    token = secrets.token_urlsafe(32)
    await conn.execute("INSERT INTO app_sessions(token_hash,user_id,expires_at) VALUES ($1,$2,NOW()+INTERVAL '12 hours')", digest(token), user_id)
    response.set_cookie(COOKIE, token, max_age=43200, httponly=True, secure=SECURE, samesite="strict", path="/")
    response.headers["Cache-Control"] = "no-store"


@router.post("/signup")
async def signup(body: Credentials, request: Request, response: Response):
    same_origin(request)
    await throttle(request, body.username)
    hashed = await hash_password(body.password)
    conn = await get_conn()
    try:
        try:
            row = await conn.fetchrow("INSERT INTO app_users(username,password_hash) VALUES ($1,$2) RETURNING id,username,wallet_address", body.username, hashed)
        except asyncpg.UniqueViolationError:
            raise HTTPException(409, "That username is unavailable") from None
        await new_session(conn, request, response, row["id"])
        return dict(row)
    finally:
        await conn.close()


@router.post("/login")
async def login(body: Credentials, request: Request, response: Response):
    same_origin(request)
    await throttle(request, body.username)
    conn = await get_conn()
    try:
        row = await conn.fetchrow("SELECT * FROM app_users WHERE username=$1", body.username)
        stored = row["password_hash"] if row else "00"*16 + ":" + "00"*64
        candidate = await hash_password(body.password, stored.split(":")[0])
        if not hmac.compare_digest(candidate, stored):
            raise HTTPException(401, "Invalid username or password")
        await new_session(conn, request, response, row["id"])
        return {key: row[key] for key in ("id", "username", "wallet_address")}
    finally:
        await conn.close()


@router.get("/me")
async def me(response: Response, user=Depends(current_user)):
    response.headers["Cache-Control"] = "no-store"
    return user


@router.post("/logout")
async def logout(request: Request, response: Response):
    same_origin(request)
    conn = await get_conn()
    try:
        await conn.execute("DELETE FROM app_sessions WHERE token_hash=$1", digest(request.cookies.get(COOKIE, "")))
    finally:
        await conn.close()
    response.delete_cookie(COOKIE, path="/", secure=SECURE, httponly=True, samesite="strict")
    return {"success": True}


class WalletProof(BaseModel):
    address: str = Field(max_length=42)
    signature: str = Field(max_length=132)


@router.post("/wallet/challenge")
async def wallet_challenge(request: Request, user=Depends(current_user)):
    message = f"DKM wallet verification\nOrigin: {ORIGIN}\nAccount: {user['id']}\nNonce: {secrets.token_hex(32)}\nThis links your wallet to your DKM account. No transaction or spending approval.\nExpires in 5 minutes."
    conn = await get_conn()
    try:
        await conn.execute("UPDATE app_sessions SET wallet_message=$2,challenge_expires=NOW()+INTERVAL '5 minutes' WHERE token_hash=$1", digest(request.cookies.get(COOKIE, "")), message)
    finally:
        await conn.close()
    return {"message": message}


@router.post("/wallet/verify")
async def verify_wallet(body: WalletProof, request: Request, user=Depends(current_user)):
    conn = await get_conn()
    try:
        async with conn.transaction():
            session = await conn.fetchrow("SELECT wallet_message FROM app_sessions WHERE token_hash=$1 AND expires_at>NOW() AND challenge_expires>NOW() FOR UPDATE", digest(request.cookies.get(COOKIE, "")))
            if not session or not session["wallet_message"]:
                raise HTTPException(400, "Request a new wallet challenge")
            try:
                address = Web3.to_checksum_address(body.address)
                recovered = Account.recover_message(encode_defunct(text=session["wallet_message"]), signature=body.signature)
                if recovered.lower() != address.lower():
                    raise ValueError()
            except Exception:
                raise HTTPException(400, "Wallet signature does not match") from None
            # One immutable verified wallet per account; never transfer a binding by address alone.
            row = await conn.fetchrow("SELECT wallet_address FROM app_users WHERE id=$1 FOR UPDATE", user["id"])
            if row["wallet_address"] and row["wallet_address"] != address:
                raise HTTPException(409, "This account already has a different wallet")
            try:
                await conn.execute("UPDATE app_users SET wallet_address=$2 WHERE id=$1", user["id"], address)
            except asyncpg.UniqueViolationError:
                raise HTTPException(409, "This wallet is already linked to another account") from None
            await conn.execute("UPDATE app_sessions SET wallet_message=NULL,challenge_expires=NULL WHERE token_hash=$1", digest(request.cookies.get(COOKIE, "")))
        return {**user, "wallet_address": address}
    finally:
        await conn.close()
