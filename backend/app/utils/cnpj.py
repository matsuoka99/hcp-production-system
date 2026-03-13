import re
from fastapi import HTTPException, status


def normalize_cnpj(cnpj: str) -> str:
    """
    Remove qualquer caractere que não seja dígito.
    """
    return re.sub(r"\D", "", cnpj or "")


def validate_cnpj_digits(cnpj: str) -> str:
    """
    Valida se o CNPJ normalizado possui 14 dígitos.
    """
    normalized = normalize_cnpj(cnpj)

    if len(normalized) != 14:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="CNPJ deve conter 14 dígitos."
        )

    return normalized


def format_cnpj(cnpj: str) -> str:
    """
    Formata um CNPJ de 14 dígitos para o padrão 00.000.000/0000-00.
    """
    normalized = normalize_cnpj(cnpj)

    if len(normalized) != 14:
        return cnpj

    return (
        f"{normalized[0:2]}."
        f"{normalized[2:5]}."
        f"{normalized[5:8]}/"
        f"{normalized[8:12]}-"
        f"{normalized[12:14]}"
    )