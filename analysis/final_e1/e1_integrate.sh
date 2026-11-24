#!/usr/bin/env bash
# E1 결과 반영 절차 (고컴, 2026-11-24). 원고는 수정하지 않는다. 반영 제안서만 만든다.
#   bash analysis/final_e1/e1_integrate.sh
# 1) origin/main을 현재 브랜치에 병합한다 (승컴 결과 수신. 실험일지 충돌은 양쪽 보존, 승컴 쪽 먼저).
# 2) e1_analyze.py: 유효성(YCSB 실패율, SQLITE_FULL, INVALID 목록), 300k/600k 분리, n<3 통계 금지
# 3) table8_e1.py: 세 정책 모두 유효 3회일 때만 표 8·그림 10 생성, 아니면 "대기"
# 4) e1_insert_proposal.py: 원고 삽입 위치별 제안서 (수치는 표 8 산출물에서만 가져온다)
# 5) check_outputs.py --paper, manuscript_audit.py
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"
git fetch -q origin
if ! git merge --no-edit -q origin/main; then
  if git status --short | grep -q '^UU EXPERIMENT_LOG.md' && [ "$(git status --short | grep -c '^UU')" = 1 ]; then
    python3 - <<'EOF'
p='EXPERIMENT_LOG.md'; L=open(p).read().split('\n')
a=L.index('<<<<<<< HEAD'); m=L.index('======='); b=next(i for i,x in enumerate(L) if x.startswith('>>>>>>> '))
L=L[:a]+L[m+1:b]+['']+L[a+1:m]+L[b+1:]; open(p,'w').write('\n'.join(L))
EOF
    git add EXPERIMENT_LOG.md && git commit -q --no-edit
  else
    echo "merge conflict outside EXPERIMENT_LOG.md: stop"; exit 1
  fi
fi
ls result/revision-20261124/mixR 2>/dev/null | head -20 || true
python3 -I analysis/final_e1/e1_analyze.py > /dev/null
python3 -I analysis/final_e1/table8_e1.py
python3 -I analysis/final_e1/e1_insert_proposal.py
python3 -I analysis/final_e1/check_outputs.py --paper | tail -1
python3 -I analysis/final_e1/manuscript_audit.py > /dev/null && echo "audit: report/final-e1-validation/manuscript_audit.md"
