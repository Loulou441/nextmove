#!/usr/bin/env bash

# Vérification statique de l'intégration LLM iOS.
# Aucun fichier modifié, aucune clé affichée, aucun appel réseau.
#
# Utilisation :
#   bash scripts/verify_llm_setup.sh
#
# Codes de sortie :
#   0 : vérifications obligatoires réussies
#   1 : fichier ou branchement obligatoire manquant

set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd -- "$SCRIPT_DIR/.." && pwd)"

errors=0
warnings=0

ok() {
    printf '[OK] %s\n' "$1"
}

warn() {
    printf '[AVERTISSEMENT] %s\n' "$1"
    warnings=$((warnings + 1))
}

fail() {
    printf '[ERREUR] %s\n' "$1"
    errors=$((errors + 1))
}

check_file() {
    local relative_path="$1"

    if [[ -f "$REPO_ROOT/$relative_path" ]]; then
        ok "$relative_path"
    else
        fail "Fichier manquant : $relative_path"
    fi
}

check_pattern() {
    local relative_path="$1"
    local pattern="$2"
    local description="$3"
    local absolute_path="$REPO_ROOT/$relative_path"

    # L'absence du fichier est déjà signalée par check_file.
    if [[ ! -f "$absolute_path" ]]; then
        return 0
    fi

    if grep -Fq -- "$pattern" "$absolute_path"; then
        ok "$description"
    else
        fail "$description : référence introuvable dans $relative_path"
    fi
}

printf 'Vérification de l’intégration LLM iOS NextMove\n'
printf 'Racine du dépôt : %s\n\n' "$REPO_ROOT"

required_files=(
    "ios/nextmove.xcodeproj/project.pbxproj"
    "ios/nextmove/Services/ConfigurationManager.swift"
    "ios/nextmove/Services/LLMService.swift"
    "ios/nextmove/Services/CoachingEngine.swift"
    "ios/nextmove/Services/EnhancedCoachingEngine.swift"
    "ios/nextmove/Services/AnalysisPipeline.swift"
    "ios/nextmove/Services/AnalysisPipeline+LLM.swift"
    "ios/nextmove/ViewModels/RecordingViewModel.swift"
    "ios/nextmoveTests/LLMServiceTests.swift"
    "ios/nextmoveTests/ConfigurationManagerTests.swift"
)

printf '%s\n' '--- Fichiers du projet ---'

for relative_path in "${required_files[@]}"; do
    check_file "$relative_path"
done

printf '\n%s\n' '--- Branchements du coaching ---'

check_pattern \
    "ios/nextmove/ViewModels/RecordingViewModel.swift" \
    "AnalysisPipeline.withLLMCoaching" \
    "RecordingViewModel référence le pipeline avec coaching LLM"

check_pattern \
    "ios/nextmove/Services/AnalysisPipeline+LLM.swift" \
    "EnhancedCoachingEngine" \
    "Le pipeline référence EnhancedCoachingEngine"

check_pattern \
    "ios/nextmove/Services/EnhancedCoachingEngine.swift" \
    "LLMService" \
    "Le moteur de coaching référence LLMService"

check_pattern \
    "ios/nextmove/Services/ConfigurationManager.swift" \
    "OPENAI_API_KEY" \
    "ConfigurationManager prend en charge OPENAI_API_KEY"

printf '\n%s\n' '--- Configuration locale ---'

# Présence dans ce terminal uniquement.
# Le .env n'est ni lu ni exécuté.
if [[ -n "${OPENAI_API_KEY:-}" ]]; then
    ok "OPENAI_API_KEY est présente dans l’environnement du terminal."
    printf '%s\n' \
        'Sa valeur et sa validité ne sont pas vérifiées.' \
        'Sa présence ici ne garantit pas sa transmission à Xcode.'
else
    warn "OPENAI_API_KEY est absente de l’environnement de ce terminal."
    printf '%s\n' \
        'Elle peut être configurée séparément dans le schéma Xcode :' \
        'Product → Scheme → Edit Scheme → Run → Arguments → Environment Variables.'
fi

if [[ -f "$REPO_ROOT/.env" ]]; then
    printf '%s\n' \
        'Un .env existe à la racine ; il n’est pas lu automatiquement par iOS.'
fi

printf '\n%s\n' '--- Documentation ---'

if [[ -f "$REPO_ROOT/docs/ios/USAGE_EXAMPLE_LLM.swift" ]]; then
    ok "Exemple disponible dans docs/ios/USAGE_EXAMPLE_LLM.swift"
else
    warn "Exemple absent : docs/ios/USAGE_EXAMPLE_LLM.swift"
fi

printf '\nRésultat : %s erreur(s), %s avertissement(s).\n' \
    "$errors" "$warnings"

if [[ "$errors" -gt 0 ]]; then
    printf '%s\n' 'Corriger les erreurs avant de poursuivre.'
    exit 1
fi

printf '\n%s\n' \
    'Les vérifications statiques obligatoires sont réussies.' \
    'Ce résultat ne valide ni la compilation ni les appels LLM.' \
    'Ouvrir ios/nextmove.xcodeproj, compiler et exécuter les tests dans Xcode.'

exit 0