from datetime import datetime, timedelta, timezone
from pathlib import Path

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID


CERT_DIR = Path(__file__).resolve().parent / "certs"

KEY_FILE = CERT_DIR / "server.key"
CERT_FILE = CERT_DIR / "server.crt"


def generate_certificate():
    CERT_DIR.mkdir(exist_ok=True)

    print("Generating NEXIS development TLS certificate...")

    # Generate RSA private key
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )

    # Certificate identity
    subject = issuer = x509.Name([
        x509.NameAttribute(
            NameOID.COMMON_NAME,
            "NEXIS-PC",
        ),
    ])

    certificate = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(private_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(
            datetime.now(timezone.utc)
        )
        .not_valid_after(
            datetime.now(timezone.utc)
            + timedelta(days=365)
        )
        .add_extension(
            x509.SubjectAlternativeName([
                x509.DNSName("localhost"),
                x509.IPAddress(
                    __import__("ipaddress").ip_address("127.0.0.1")
                ),
            ]),
            critical=False,
        )
        .sign(
            private_key,
            hashes.SHA256(),
        )
    )

    # Save private key
    KEY_FILE.write_bytes(
        private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption(),
        )
    )

    # Save certificate
    CERT_FILE.write_bytes(
        certificate.public_bytes(
            serialization.Encoding.PEM
        )
    )

    print()
    print("TLS CERTIFICATE CREATED")
    print("=" * 60)
    print("Private key :", KEY_FILE)
    print("Certificate :", CERT_FILE)
    print("Valid       : 365 days")
    print("=" * 60)


if __name__ == "__main__":
    generate_certificate()