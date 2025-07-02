# Modelo de Score de Risco de Crédito - Empréstimos Pessoais

## Descrição

Modelo supervisionado para prever a probabilidade de inadimplência em até 90 dias após a concessão de empréstimos pessoais não-garantidos. O objetivo é apoiar decisões de aprovação automática ou assistida, calibrando o risco de carteira.

---

## Hipótese principal

Clientes com características demográficas, financeiras e comportamentais específicas têm probabilidade significativamente diferente de inadimplência, e um modelo estatístico pode quantificar essa diferença para melhorar a decisão de crédito.

---

## Benefício esperado

- Redução do índice de inadimplência (NPL) em novos créditos.
- Otimização do volume concedido mantendo risco controlado.
- Automatização e padronização do processo de crédito.
- Melhora na rentabilidade ao precificar risco de forma mais granular.

---

## Hipóteses testadas

- Variáveis demográficas (idade, estado civil) têm valor preditivo para inadimplência.
- Indicadores de renda e comprometimento mensal melhoram o modelo.
- Comportamento histórico de pagamento (score externo, atrasos anteriores) é o maior driver de risco.
- Features derivadas de conta corrente (saldo médio, uso de limite) agregam valor marginal.
- Técnicas não lineares (árvores, boosting) superam regressão logística simples em AUC.

---

## Conjuntos de dados avaliados

- Base histórica de contratos (5 anos), ~500.000 linhas.
- Dados cadastrais do cliente no onboarding.
- Histórico de transações de conta corrente (para subset com conta no banco).
- Bureau de crédito externo (score, negativações, consultas).
- Labels de inadimplência (default 90+).

---

## Técnicas analisadas

- Regressão logística (baseline)
- Random Forest
- XGBoost
- LightGBM
- Redes neurais rasas (MLP)
- Calibração de probabilidade via Platt scaling e isotonic regression

---

## Constatações e hipóteses validadas

- Variáveis comportamentais de histórico de pagamento têm maior importância (top 5 features).
- Dados de conta corrente são muito preditivos mas só disponíveis para ~60% dos clientes.
- Regressão logística bem calibrada é competitiva (AUC ~0.76) mas perde para boosting.
- XGBoost e LightGBM tiveram AUC ~0.81 sem overfitting perceptível.
- Overfitting observado em redes neurais sem regularização agressiva.
- Calibração pós-treinamento melhorou Brier Score em todos os modelos.

---

## Resultados

- Melhor modelo escolhido: LightGBM
- AUC validado: 0.81
- Brier Score validado: 0.138
- Feature Importance: score externo, atraso anterior, renda declarada, saldo médio em conta, uso de limite.
- Modelo calibrado pronto para produção com corte sugerido para política conservadora (default rate target ~5%).

---

## Considerações e preocupações

- Drift potencial em dados de renda declarada.
- Cobertura incompleta de dados de conta corrente limita uso universal.
- Dependência de bureau externo (custo, SLA, regulamentação).
- Explicabilidade: árvores de boosting são menos transparentes que regressão.
- Regulamentação local exige explicação de decisão de crédito (contrapontos para fairness/ética).

---

## Próximos passos

- Monitoramento de PSI/KS para drift mensal.
- Ajustar cortes de score conforme estratégia de risco.
- Testar fairness e bias (grupos protegidos).
- Investigar blending com score de bureau.
- Planejar atualização/retreinamento semestral.
