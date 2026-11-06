"""Transforma um usuário em técnico. Uso: uv run python -m app.auth.promover email@exemplo.com"""

import sys

from sqlalchemy import select

from app.auth.modelos import Perfil, Usuario
from app.banco import SessaoLocal


def main() -> None:
    if len(sys.argv) != 2:
        sys.exit("Uso: uv run python -m app.auth.promover email@exemplo.com")

    email = sys.argv[1].lower()
    with SessaoLocal() as sessao:
        usuario = sessao.scalar(select(Usuario).where(Usuario.email == email))
        if usuario is None:
            sys.exit(f"Usuário {email} não encontrado.")
        usuario.perfil = Perfil.TECNICO
        sessao.commit()
    print(f"{email} agora é técnico.")


if __name__ == "__main__":
    main()
