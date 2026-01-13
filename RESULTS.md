# Résultats de Validation

Ce document synthétise les résultats obtenus lors de l'exécution des modules d'analyse sur les données extraites depuis une base Oracle réelle.

## 1. Détection d'Anomalies (`detected_anomalies.json`)

Le module a analysé les logs d'accès récents.

- **Total analysé** : 50+ logs
- **Résultat** : Détection de **2 comportements SUSPECTS**.

| Timestamp        | Classification | Justification IA                           | Sévérité |
| ---------------- | -------------- | ------------------------------------------ | -------- |
| 2026-01-12 15:07 | NORMAL         | Connexion standard compte SYSTEM           | 0        |
| 2026-01-12 15:07 | SUSPECT        | Échec création table (RETURNCODE 955)      | 6        |
| 2026-01-12 15:07 | SUSPECT        | Accès répétitifs aux dictionnaires système | 7        |

> **Analyse** : L'IA a correctement identifié des tentatives de reconnaissance (scan de dictionnaire) et des erreurs suspectes qui pourraient indiquer une tentative d'intrusion ou de mapping.

## 2. Optimisation SQL (`query_analysis.json`)

Analyse des Top-3 requêtes les plus lentes (ou critiques) identifiées dans `performance_metrics.csv`.

### Exemple : Requête `guw87u8x36z8r`

- **Problème** : Plan d'exécution `UNKNOWN` (Statistiques manquantes), risque de _Full Table Scan_ sur mise à jour.
- **Recommandations IA** :
  1. **Création d'Index** : `CREATE INDEX ... ON WRI$_SQLSET_PLANS(STMT_ID, PLAN_HASH_VALUE)`
  2. **Statistiques** : `DBMS_STATS.GATHER_TABLE_STATS...`
- **Gain Estimé** : **75%**

### Exemple : Requête `16cffsk1wdzcc`

- **Problème** : Filtre sur `USER#` sans certitude d'utilisation d'index.
- **Recommandations IA** : Vérifier index `I_USER1` et forcer via Hint `/*+ INDEX(u I_USER1) */`.

## 3. Audit de Sécurité (`last_audit.json`)

Autodiagnostic basé sur les configurations extraites (`DBA_USERS`, `DBA_ROLES`).

- **Score Global** : **65/100** (Niveau : Moyen/Risqué)
- **Top Risques Identifiés** :
  - 🚨 **CRITIQUE** : Privilèges `DROP ANY` et `GRANT ANY` accordés excessivement (notamment au rôle DBA et IMP_FULL).
  - ⚠️ **ÉLEVÉ** : Absence de protection par mot de passe pour les rôles (DBA, CONNECT...).
  - ⚠️ **ÉLEVÉ** : Profils de sécurité par défaut (pas de rotation de mot de passe forcée).

**Plan d'Action Suggéré** :

1. Révoquer les droits `ANY` non essentiels.
2. Activer `PASSWORD_REQUIRED='YES'` pour les rôles sensibles.
3. Créer des profils utilisateurs stricts (verrouillage après échecs).

## 4. Stratégie de Sauvegarde (`backup_plan.json`)

Basé sur la volumétrie et la criticité (Rôle DBA détecté, Transactions élevées).

- **Stratégie** : Incrémentale Niveau 1 + Archivage continu.
- **Fréquence** : Complète Hebdo + Incrémentale Quotidienne.
- **RTO/RPO** : Orienté haute disponibilité.
- **Script RMAN** : Généré automatiquement dans `data/backup_script.rman`.

---

## Conclusion

Le système a démontré sa capacité à :

1. **Ingérer** des données hétérogènes (Logs, SQL, Config).
2. **Contextualiser** via RAG (compréhension des codes erreurs ORA-, des vues dictionnaire).
3. **Produire** des rapports actionnables et justifiés par l'IA.
