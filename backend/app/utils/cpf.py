import re
from fastapi import HTTPException, status


def normalize_cpf(cpf: str) -> str:
    """
    Remove qualquer caractere que não seja dígito.
    """
    return re.sub(r"\D", "", cpf or "")


def validate_cpf_digits(cpf: str) -> str:
    """
    Valida se o CPF normalizado possui 11 dígitos.
    """
    normalized = normalize_cpf(cpf)

    if len(normalized) != 11:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="CPF deve conter 11 dígitos."
        )

    return normalized


def format_cpf(cpf: str) -> str:
    """
    Formata um CPF de 11 dígitos para o padrão 000.000.000-00.
    """
    normalized = normalize_cpf(cpf)

    if len(normalized) != 11:
        return cpf

    return (
        f"{normalized[0:3]}."
        f"{normalized[3:6]}."
        f"{normalized[6:9]}-"
        f"{normalized[9:11]}"
    )