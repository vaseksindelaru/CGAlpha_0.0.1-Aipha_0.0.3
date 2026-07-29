## Resumen de sesiones pasadas

### 2026-07-29: CGAlpha Cloud Infrastructure - Sesión 2
- R2 bucket `cgalpha-data` creado vía API (cuenta 025eecf772c35797f9aef9d18359e521, EEUR)
- **R2 S3 token obtendo**: Token `REDACTED_R2_TOKEN` con credenciales S3:
  - Access Key ID: `REDACTED_R2_ACCESS_KEY`
  - Secret Access Key: `REDACTED_R2_SECRET_KEY`
- Endpoint S3: `https://025eecf772c35797f9aef9d18359e521.r2.cloudflarestorage.com`
- rclone `cgalpha-r2` S3 remote configurado y **funcionando** (ListObjectsV2 OK, 200)
- Bucket `cgalpha-data` tiene 0 objetos (vacío)
- rclone `cgalpha-b2` remoto eliminado (ya no funciona, auth 401)
- B2 auth con nueva key (K003DK+hf...) de otro Backblaze account (003...03) sigue devolviendo 401 - el bucket está en el account 003...01