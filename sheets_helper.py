import os
import json
from google.oauth2 import service_account
from googleapiclient.discovery import build

DRIVE_FOLDER_ID = os.environ.get("DRIVE_FOLDER_ID", "10J9gF-P8sGmVLuSjwk_F864ZZ5cYQSLb")
SCOPES = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
SHEET_NAME = "DRIVV Prospectos"
HEADERS = ["Fecha", "Ronda", "Negocio", "Email", "Rubro", "Oportunidad", "Hallazgo", "Estado"]

def _creds():
    info = json.loads(os.environ["SERVICE_ACCOUNT_JSON"])
    return service_account.Credentials.from_service_account_info(info, scopes=SCOPES)

def obtener_o_crear_planilla():
    creds = _creds()
    drive = build("drive", "v3", credentials=creds)
    sheets = build("sheets", "v4", credentials=creds)

    q = f"'{DRIVE_FOLDER_ID}' in parents and mimeType='application/vnd.google-apps.spreadsheet' and trashed=false"
    res = drive.files().list(q=q, fields="files(id, name)").execute()
    files = res.get("files", [])
    if not files:
        raise RuntimeError(
            "No hay ninguna hoja de calculo dentro de la carpeta DRIVV Prospectos todavia. "
            "Creala desde adentro de esa carpeta en Drive (+ Nuevo > Google Sheets)."
        )
    sheet_id = files[0]["id"]

    if files[0]["name"] != SHEET_NAME:
        drive.files().update(fileId=sheet_id, body={"name": SHEET_NAME}).execute()

    existente = sheets.spreadsheets().values().get(spreadsheetId=sheet_id, range="A1:A1").execute()
    if not existente.get("values"):
        sheets.spreadsheets().values().update(
            spreadsheetId=sheet_id, range="A1",
            valueInputOption="RAW", body={"values": [HEADERS]}
        ).execute()
    return sheet_id

def emails_ya_registrados(sheet_id):
    creds = _creds()
    sheets = build("sheets", "v4", credentials=creds)
    result = sheets.spreadsheets().values().get(spreadsheetId=sheet_id, range="D2:D1000").execute()
    valores = result.get("values", [])
    return set(v[0].lower() for v in valores if v)

def agregar_prospectos(sheet_id, filas):
    creds = _creds()
    sheets = build("sheets", "v4", credentials=creds)
    sheets.spreadsheets().values().append(
        spreadsheetId=sheet_id, range="A1",
        valueInputOption="RAW", insertDataOption="INSERT_ROWS",
        body={"values": filas}
    ).execute()

def leer_filas(sheet_id):
    """Devuelve la lista de filas de datos (sin encabezado). Cada fila trae ademas
    su numero de fila real en la planilla como ultimo elemento (para poder actualizarla)."""
    creds = _creds()
    sheets = build("sheets", "v4", credentials=creds)
    result = sheets.spreadsheets().values().get(spreadsheetId=sheet_id, range="A2:H1000").execute()
    valores = result.get("values", [])
    filas = []
    for i, fila in enumerate(valores):
        fila = fila + [""] * (8 - len(fila))
        filas.append(fila + [i + 2])
    return filas

def actualizar_estado(sheet_id, numero_de_fila, nuevo_estado):
    """numero_de_fila es el numero real de fila en la planilla (columna H de esa fila)."""
    creds = _creds()
    sheets = build("sheets", "v4", credentials=creds)
    sheets.spreadsheets().values().update(
        spreadsheetId=sheet_id, range=f"H{numero_de_fila}",
        valueInputOption="RAW", body={"values": [[nuevo_estado]]}
    ).execute()

if __name__ == "__main__":
    sid = obtener_o_crear_planilla()
    print(f"Planilla lista: https://docs.google.com/spreadsheets/d/{sid}")
    print(f"Emails ya registrados: {emails_ya_registrados(sid)}")
