"""
Envoi d'emails transactionnels via Resend — vérification de compte à
l'inscription, et réinitialisation de mot de passe oublié.

Utilise l'adresse d'expédition de test de Resend (onboarding@resend.dev),
suffisante en développement/démo ; un domaine propre vérifié serait
nécessaire pour un envoi public à grande échelle.
"""
import os

import resend

FROM_ADDRESS = "NextMove <noreply@nextmoveapp.lol>"


def _ensure_api_key() -> None:
    """Lit la clé à chaque appel plutôt qu'une seule fois à l'import du
    module — évite une dépendance à l'ordre d'import des autres fichiers
    qui chargent le .env (config.py)."""
    resend.api_key = os.environ.get("RESEND_API_KEY")


class EmailSendError(Exception):
    """Levée quand l'envoi d'email échoue (clé manquante, erreur Resend...)."""


def send_verification_code(to_email: str, code: str) -> None:
    """Envoie le code à 6 chiffres pour confirmer la création d'un compte."""
    _ensure_api_key()
    if not resend.api_key:
        raise EmailSendError("RESEND_API_KEY manquante dans .env")
    try:
        resend.Emails.send({
            "from": FROM_ADDRESS,
            "to": to_email,
            "subject": "Confirme ton compte NextMove",
            "html": f"""
                <div style="font-family: sans-serif; max-width: 480px; margin: 0 auto;">
                    <h2 style="color: #34C759;">Bienvenue sur NextMove 🏓</h2>
                    <p>Voici ton code de confirmation :</p>
                    <p style="font-size: 32px; font-weight: bold; letter-spacing: 4px;">{code}</p>
                    <p style="color: #8E8E93; font-size: 13px;">Ce code expire dans 15 minutes.</p>
                </div>
            """,
        })
    except Exception as exc:
        raise EmailSendError(f"Échec de l'envoi de l'email : {exc}") from exc


def send_password_reset_code(to_email: str, code: str) -> None:
    """Envoie le code à 6 chiffres pour réinitialiser un mot de passe oublié."""
    _ensure_api_key()
    if not resend.api_key:
        raise EmailSendError("RESEND_API_KEY manquante dans .env")
    try:
        resend.Emails.send({
            "from": FROM_ADDRESS,
            "to": to_email,
            "subject": "Réinitialise ton mot de passe NextMove",
            "html": f"""
                <div style="font-family: sans-serif; max-width: 480px; margin: 0 auto;">
                    <h2 style="color: #1C1C1E;">Réinitialisation de mot de passe</h2>
                    <p>Voici ton code de réinitialisation :</p>
                    <p style="font-size: 32px; font-weight: bold; letter-spacing: 4px;">{code}</p>
                    <p style="color: #8E8E93; font-size: 13px;">Ce code expire dans 15 minutes. Si tu n'es pas à l'origine de cette demande, ignore cet email.</p>
                </div>
            """,
        })
    except Exception as exc:
        raise EmailSendError(f"Échec de l'envoi de l'email : {exc}") from exc