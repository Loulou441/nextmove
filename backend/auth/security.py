"""
Hashing et vérification des mots de passe.

Utilise directement la librairie bcrypt (pas passlib, qui n'est plus
maintenu depuis 2020 et casse avec les versions récentes de bcrypt).
Chaque mot de passe est haché avec un "salt" aléatoire différent à
chaque fois : deux utilisateurs avec le même mot de passe auront des
hash différents en base — c'est le standard pour ne jamais stocker de
mot de passe en clair.
"""

import bcrypt

# bcrypt ignore silencieusement tout ce qui dépasse 72 bytes : on tronque
# nous-mêmes en amont pour que le comportement soit explicite et prévisible.
_MAX_PASSWORD_BYTES = 72


def hash_password(plain_password: str) -> str:
    """Transforme un mot de passe en clair en hash sécurisé à stocker en BDD."""
    password_bytes = plain_password.encode("utf-8")[:_MAX_PASSWORD_BYTES]
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Vérifie qu'un mot de passe en clair correspond au hash stocké."""
    password_bytes = plain_password.encode("utf-8")[:_MAX_PASSWORD_BYTES]
    return bcrypt.checkpw(password_bytes, hashed_password.encode("utf-8"))