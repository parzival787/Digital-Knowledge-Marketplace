"""Plot retained measurements using the bundled ReportLab chart library."""
import json
from pathlib import Path
from reportlab.graphics.shapes import Drawing, String, Rect
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics import renderSVG
from reportlab.lib.colors import HexColor

folder = Path(__file__).resolve().parent
results = json.loads((folder.parents[1] / 'research_results/vqc_embeddings.json').read_text())
modes = ['original', 'classical', 'untrained', 'trained']
assert sum(q['split'] == 'test' for q in results['queries']) == 16
assert sum(q['split'] == 'validation' for q in results['queries']) == 16
chart = VerticalBarChart()
chart.x, chart.y, chart.width, chart.height = 65, 92, 620, 260
chart.data = [[results['summary'][split][mode] for mode in modes] for split in ['validation', 'test']]
assert all(0 <= v <= 1 for row in chart.data for v in row)
chart.categoryAxis.categoryNames = ['MiniLM 384D', 'PCA4 + expansion', 'Untrained VQC', 'Trained VQC']
chart.categoryAxis.labels.fontSize = 10
chart.valueAxis.valueMin, chart.valueAxis.valueMax, chart.valueAxis.valueStep = 0, 1, .2
chart.bars[0].fillColor = HexColor('#39789D')
chart.bars[1].fillColor = HexColor('#C87935')
chart.bars.strokeColor = None
chart.barLabelFormat = '%.4f'
chart.barLabels.fontSize = 9
chart.barLabels.nudge = 6
chart.groupSpacing = 22
chart.barSpacing = 4
figure = Drawing(740, 440)
figure.add(String(370, 411, 'Retrieval quality on the controlled DKM embedding benchmark', textAnchor='middle', fontSize=14))
figure.add(String(20, 360, 'NDCG@10', fontSize=10))
for x, name, color in [(438,'Validation','#39789D'),(560,'Test','#C87935')]:
 figure.add(Rect(x,378,11,11,fillColor=HexColor(color),strokeColor=None))
 figure.add(String(x+17,379,name,fontSize=10))
figure.add(chart)
figure.add(String(370,40,'96 authored documents; 16 validation and 16 test queries.',textAnchor='middle',fontSize=10))
figure.add(String(370,23,'Classical statevector simulation; single-run results, no confidence intervals.',textAnchor='middle',fontSize=10))
renderSVG.drawToFile(figure,str(folder/'DKM_VQC_Retrieval_Results.svg'))
print('Saved SVG from retained measured results; no experiments rerun.')
