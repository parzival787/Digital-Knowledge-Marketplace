KNOWLEDGE_ASSET_ABI = [
    {
        "inputs": [
            {
                "internalType": "uint256",
                "name": "tokenId",
                "type": "uint256",
            }
        ],
        "name": "ownerOf",
        "outputs": [
            {
                "internalType": "address",
                "name": "",
                "type": "address",
            }
        ],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [
            {
                "internalType": "uint256",
                "name": "tokenId",
                "type": "uint256",
            }
        ],
        "name": "getAsset",
        "outputs": [
            {
                "components": [
                    {
                        "internalType": "string",
                        "name": "ipfsCID",
                        "type": "string",
                    },
                    {
                        "internalType": "string",
                        "name": "metadataCID",
                        "type": "string",
                    },
                    {
                        "internalType": "uint256",
                        "name": "priceUSDC",
                        "type": "uint256",
                    },
                    {
                        "internalType": "address",
                        "name": "creator",
                        "type": "address",
                    },
                    {
                        "internalType": "uint8",
                        "name": "license",
                        "type": "uint8",
                    },
                    {
                        "internalType": "uint8",
                        "name": "qualityScore",
                        "type": "uint8",
                    },
                    {
                        "internalType": "bool",
                        "name": "active",
                        "type": "bool",
                    },
                    {
                        "internalType": "uint40",
                        "name": "mintedAt",
                        "type": "uint40",
                    },
                ],
                "internalType": "struct KnowledgeAsset.Asset",
                "name": "",
                "type": "tuple",
            }
        ],
        "stateMutability": "view",
        "type": "function",
    },
]