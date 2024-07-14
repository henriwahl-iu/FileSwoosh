# Get the first argument passed to the script, which is the file to be signed
$file = $args[0]

# Convert the base64 encoded certificate stored in the environment variable to a byte array
$cert_buffer = [System.Convert]::FromBase64String($env:WIN_SIGNING_CERT_BASE64)

# Create a new X509Certificate2 object using the byte array and the password stored in the environment variable
$cert = [System.Security.Cryptography.X509Certificates.X509Certificate2]::New($cert_buffer, $env:WIN_SIGNING_PASSWORD)

# Sign the file using the certificate, SHA256 as the hash algorithm, and the Sectigo timestamp server
Set-AuthenticodeSignature -HashAlgorithm SHA256 -Certificate $cert -TimestampServer http://timestamp.sectigo.com -FilePath $file