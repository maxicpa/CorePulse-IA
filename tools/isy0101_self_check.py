from __future__ import annotations
import json, sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "core"))

from corepulse_ai.pipeline import CorePulseAIPipeline
from corepulse_ai.providers import LLMProvider, MockProvider

class AdversarialProvider(LLMProvider):
    provider_name="adversarial-test"; model_name="intentional-hallucination"; is_real_llm=False
    def generate(self, prompt: str) -> str:
        return json.dumps({
            "measured_data":{"cpu_temperature":"81 °C"},
            "interpretation":"La CPU está a 81 °C y presenta temperatura elevada.",
            "retrieved_information":["Información técnica recuperada [S1]."],
            "recommendations":["Revisar refrigeración [S1]."],
            "sources":[{"id":"S999","title":"inventada","source":"inventada"}],
        }, ensure_ascii=False)

def load(name):
    return json.loads((ROOT/'examples/corepulse_ai'/name).read_text(encoding='utf-8'))

def check(name, ok, detail): return {'name':name,'passed':bool(ok),'detail':detail}

def run():
    knowledge=ROOT/'knowledge/corepulse_ai'; checks=[]
    required=[ROOT/'core/corepulse_ai/pipeline.py', ROOT/'core/corepulse_ai/prompts.py',
              ROOT/'core/corepulse_ai/retriever.py', ROOT/'core/corepulse_ai/validator.py',
              knowledge/'internal_corepulse.json', knowledge/'external_controlled.json']
    missing=[str(p.relative_to(ROOT)) for p in required if not p.exists()]
    checks.append(check('estructura_academica', not missing, 'OK' if not missing else ', '.join(missing)))

    pipe=CorePulseAIPipeline(MockProvider(), knowledge)
    cases=[
      ('cpu','Analiza CPU y temperatura.','telemetry_cpu_hot.json'),
      ('gpu','Analiza GPU y temperatura.','telemetry_gpu_load.json'),
      ('memory','Analiza RAM y memoria.','telemetry_memory_high.json'),
      ('storage','Analiza SSD y almacenamiento.','telemetry_storage_high.json'),
      ('network','Analiza latencia de red y ping.','telemetry_network_latency.json'),
      ('system','Analiza salud del sistema Windows.','telemetry_system_mixed.json'),
      ('general','Dame una evaluación general del equipo.','telemetry_general.json'),
    ]
    for expected, query, filename in cases:
        result=pipe.run(query, load(filename)); types={x['type'] for x in result['retrieved_sources']}
        ok=(result['route']==expected and result['validation']['valid'] and len(result['retrieved_sources'])<=4
            and {'internal','external'}.issubset(types))
        checks.append(check(f'ruta_{expected}', ok, f"route={result['route']}; fuentes={len(result['retrieved_sources'])}; tipos={','.join(sorted(types))}"))

    hot=pipe.run('Analiza CPU y temperatura.', load('telemetry_cpu_hot.json'))
    checks.append(check('telemetria_cpu_exacta', hot['measured_data']['cpu_usage']=='96 %' and hot['measured_data']['cpu_temperature']=='94 °C' and hot['measured_data']['ram_usage']=='72 %', json.dumps(hot['measured_data'], ensure_ascii=False)))
    amd_ids={x['chunk_id'] for x in hot['retrieved_sources']}
    checks.append(check('rag_amd_sin_intel', any(i.startswith('EXT-AMD-') for i in amd_ids) and not any(i.startswith('EXT-INTEL-') for i in amd_ids), ','.join(sorted(amd_ids))))

    na=pipe.run('Analiza CPU sin inventar temperatura.', load('telemetry_cpu_na.json'))
    checks.append(check('real_or_na_conservado', na['measured_data']['cpu_temperature']=='N/A' and na['validation']['valid'], json.dumps(na['validation'], ensure_ascii=False)))
    adv=CorePulseAIPipeline(AdversarialProvider(), knowledge).run('Analiza CPU.', load('telemetry_cpu_na.json'))
    detected=(adv['measured_data']['cpu_temperature']=='N/A' and not adv['validation']['valid'] and any('cpu_temperature' in e for e in adv['validation']['errors']))
    checks.append(check('alucinacion_na_detectada', detected, json.dumps(adv['validation'], ensure_ascii=False)))

    passed=all(c['passed'] for c in checks)
    report={'schema_version':'ep1-final-self-check-1','generated_at_utc':datetime.now(timezone.utc).isoformat(),
            'project':'CorePulse-IA / ISY0101','all_passed':passed,'checks':checks}
    out=ROOT/'evidence/pruebas'; out.mkdir(parents=True, exist_ok=True)
    (out/'self_check.json').write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n',encoding='utf-8')
    lines=['CorePulse-IA · Self-check EP1','='*31]
    for c in checks: lines.append(f"[{'PASS' if c['passed'] else 'FAIL'}] {c['name']}: {c['detail']}")
    lines += ['', f"RESULTADO: {'PASS' if passed else 'FAIL'}"]
    (out/'self_check.txt').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print('\n'.join(lines)); return 0 if passed else 2

if __name__=='__main__': raise SystemExit(run())
