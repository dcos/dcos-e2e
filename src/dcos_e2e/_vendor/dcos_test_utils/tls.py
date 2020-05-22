import datetime
import uuid

import cryptography.hazmat.backends
from collections import OrderedDict
from cryptography import x509
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import dsa, ec, rsa
from cryptography.x509.oid import NameOID

cryptography_default_backend = cryptography.hazmat.backends.default_backend()


class CertValidationError(Exception):
    pass


def load_pem_x509_cert(cert_pem, allow_ec_cert=True):
    """
    Load X.509 certificate from the provided PEM/text representation.

    - Expect a single X.509 certificate in the "OpenSSL PEM format"
      (see https://tools.ietf.org/html/rfc7468#section-5 for format
      specification).

    - Expect that the public key of the certificate is of type RSA or EC
      (if enabled via allow_ec_cert).

    Note that if the certificate text representations contains more than one
    certificate definition, x509.load_pem_x509_certificate would silently read
    only the first one.


    Args:
        cert_pem (str): the PEM text representation of the data to verify.
        allow_ec_cert (bool): True if EC public key is supported.

    Returns:
        `cert`, an object of type `cryptography.x509.Certificate`.

    Raises:
        CertValidationError
    """

    if cert_pem.count('BEGIN CERTIFICATE') > 1:
        raise CertValidationError(
            'Certificate data contains more than one certificate definition.')

    try:
        cert = x509.load_pem_x509_certificate(
            data=cert_pem.encode('utf-8'),
            backend=cryptography_default_backend
            )
    except ValueError as e:
        raise CertValidationError('Invalid certificate: %s' % e)

    public_key = cert.public_key()

    supported_keys = OrderedDict([(rsa.RSAPublicKey, 'RSA')])
    if allow_ec_cert:
        supported_keys[ec.EllipticCurvePublicKey] = 'EC'

    if not isinstance(public_key, tuple(supported_keys.keys())):
        names = list(supported_keys.values())
        if len(names) > 1:
            names_str = ', '.join(names[:-1]) + ' or ' + names[-1]
        else:
            names_str = names[0]

        raise CertValidationError(
            'Unexpected public key type (not {})'.format(names_str))

    return cert


def cert_key_usage(**kwargs):
    """
    Helper to create x509.KeyUsage object. Function provide defaults (False)
    for unspecified KeyUsage arguments.

    Args:
        x509.KeyUsage keys. If not provided False is used for each arg.

    Return:
        x509.KeyUsage
    """
    required = [
        'digital_signature',
        'content_commitment',
        'key_encipherment',
        'data_encipherment',
        'key_agreement',
        'key_cert_sign',
        'crl_sign',
        'encipher_only',
        'decipher_only',
    ]
    for name in required:
        kwargs.setdefault(name, False)

    return x509.KeyUsage(**kwargs)


def cert_extended_key_usage(**kwargs):
    """
    Helper to create x509.ExtendedKeyUsage object.

    Args:
        x509.ExtendedKeyUsage keys. If not provided False is used for each arg.

    Return:
        x509.ExtendedKeyUsage
    """
    usages = {
        'server_auth': x509.oid.ExtendedKeyUsageOID.SERVER_AUTH,
        'client_auth': x509.oid.ExtendedKeyUsageOID.CLIENT_AUTH,
        'code_signing': x509.oid.ExtendedKeyUsageOID.CODE_SIGNING,
        # ... and others, which we do not need. Check e.g.
        # https://cryptography.io/en/latest/_modules/cryptography/x509/oid/#ExtendedKeyUsageOID
        # for details.
    }
    res = []
    for k, v in kwargs.items():
        assert k in usages, "unknown exteneded key usage specified"
        if v:
            res.append(usages[k])

    return x509.ExtendedKeyUsage(res)


def cert_name(common_name):
    """
    Create x509.Name
    """
    return x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
        x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "CA"),
        x509.NameAttribute(NameOID.LOCALITY_NAME, "San Francisco"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, "D2iQ, Inc."),
        x509.NameAttribute(NameOID.COMMON_NAME, common_name),
        ])


def ca_cert_builder(
        public_key,
        common_name="Root CA",
        issuer=None,
        basic_constraints=x509.BasicConstraints(
            ca=True, path_length=None),
        key_usage=cert_key_usage(
            key_cert_sign=True),
        subject_alternative_names=None,
        not_valid_before=None,
        not_valid_after=None,
        valid_days=3650,
        ):
    return cert_builder(
        public_key=public_key,
        common_name=common_name,
        issuer=issuer,
        basic_constraints=basic_constraints,
        key_usage=key_usage,
        subject_alternative_names=subject_alternative_names,
        not_valid_before=not_valid_before,
        not_valid_after=not_valid_after,
        valid_days=valid_days,
    )


def external_cert_builder(
        public_key,
        common_name="Web Server Cert",
        issuer=None,
        basic_constraints=x509.BasicConstraints(
            ca=False, path_length=None),
        key_usage=cert_key_usage(
            key_cert_sign=False, digital_signature=True, key_encipherment=True),
        extended_key_usage=cert_extended_key_usage(server_auth=True),
        subject_alternative_names=[
            x509.DNSName('maryna.example.com'),
        ],
        not_valid_before=None,
        not_valid_after=None,
        valid_days=3650,
        ):
    return cert_builder(
        public_key=public_key,
        common_name=common_name,
        issuer=issuer,
        basic_constraints=basic_constraints,
        key_usage=key_usage,
        extended_key_usage=extended_key_usage,
        subject_alternative_names=subject_alternative_names,
        not_valid_before=not_valid_before,
        not_valid_after=not_valid_after,
        valid_days=valid_days,
    )


def cert_builder(
        public_key,
        common_name="Root CA",
        issuer=None,
        basic_constraints=x509.BasicConstraints(ca=True, path_length=None),
        key_usage=None,
        extended_key_usage=None,
        subject_alternative_names=None,
        not_valid_before=None,
        not_valid_after=None,
        valid_days=3650,
        ):
    """
    Create cert builder with some sensible defaults.

    Args:
        public_key (str): public key of the certificate
        common_name (str): Certificate subject common name
        issuer (x509.Name): Issuer name, if not provided subject is used
        basic_constraints (x509.BasicConstraints): Custom basic constraints
            extension value
        key_usage (x509.KeyUsage): Custom key constraints extension value
        extended_key_usage (x509.ExtendedKeyUsage): The list of extended key
            usage attributes to apply
        subject_alternative_names (List[x509.IPAddress or x509.DNSName]): list
            of Subject Alternative Names to assign to the certificate
        not_valid_before (datetime): From which time is a certificate valid
        not_valid_after (datetime): After which time is certificate invalid
        valid_days (int): Number of days that cert is valid

    Returns:
        x509.CertificateBuilder
    """
    if not_valid_before is None:
        not_valid_before = datetime.datetime.utcnow()

    if not_valid_after is None:
        not_valid_after = not_valid_before + datetime.timedelta(days=valid_days)

    subject = cert_name(common_name)
    if issuer is None:
        issuer = subject

    builder = x509.CertificateBuilder().subject_name(
        subject
    ).issuer_name(
        issuer
    ).public_key(
        public_key
    ).not_valid_before(
        not_valid_before
    ).not_valid_after(
        not_valid_after
    ).serial_number(
        int(uuid.uuid4())
    )

    if basic_constraints:
        builder = builder.add_extension(basic_constraints, critical=True)

    if key_usage is not None:
        builder = builder.add_extension(key_usage, critical=True)

    if extended_key_usage is not None:
        builder = builder.add_extension(extended_key_usage, critical=True)

    if subject_alternative_names is not None:
        builder = builder.add_extension(
            x509.SubjectAlternativeName(subject_alternative_names),
            critical=True
        )

    return builder


def serialize_cert_to_pem(cert):
    """
    Serialize certificate to PEM format.

    Args:
        cert (x509.Certificate): Certificate to be serialized.

    Return:
        PEM text representing serialized certificate.
    """
    return cert.public_bytes(encoding=serialization.Encoding.PEM).decode('utf-8')


def serialize_cert_chain_to_pem(chain):
    """
    Serialize chain of certificates to PEM format string.

    Args:
        chain (List[x509.Certificate]): Chain of certificates to be serialized.

    Return:
        PEM text representing serialized certificate.
    """
    return ''.join([serialize_cert_to_pem(cert) for cert in chain])


def common_names(cert):
    return [x.value for x in cert.subject.get_attributes_for_oid(NameOID.COMMON_NAME)]


def generate_root_ca_and_intermediate_ca(
        number=1,
        ):
    """
    Helper to create root CA cert and intermediate certs.

    Args:
        number (int): Number of intermediate certs.

    Returns:
        Certificate chain with each CA certificate followed by its issuer,
        ending with the self-signed root certificate

        List[(x509.Certificate, rsa.RSAPrivateKey)]
    """
    chain = []

    root_ca_private_key = generate_rsa_private_key()
    root_ca = sign_cert_builder(
        ca_cert_builder(root_ca_private_key.public_key()),
        root_ca_private_key
        )
    chain.append((root_ca, root_ca_private_key))

    parent, parent_private_key = root_ca, root_ca_private_key
    for i in range(0, number):
        intermediate_ca_private_key = generate_rsa_private_key()
        intermediate_ca = sign_cert_builder(
            ca_cert_builder(
                intermediate_ca_private_key.public_key(),
                common_name="Intermediate CA {}".format(i),
                issuer=parent.subject,
                ),
            parent_private_key
        )
        chain.append((intermediate_ca, intermediate_ca_private_key))
        parent, parent_private_key = intermediate_ca, intermediate_ca_private_key

    return list(reversed(chain))


def generate_rsa_private_key(key_size=2048, public_exponent=65537):
    """
    Generate RSA private key.

    Args:
        key_size (int): RSA key size
        public_exponent (int): Key public exponent

    Return:
        rsa.RSAPrivateKey
    """
    return rsa.generate_private_key(
        public_exponent=public_exponent,
        key_size=key_size,
        backend=cryptography_default_backend
        )


def generate_ec_private_key(curve=None):
    """
    Generate EC private key.

    Args:
        curve (ec.EllipticCurve): EC if not provided SECP384R1 used.

    Return:
        ec.EllipticCurvePrivateKey
    """
    curve = ec.SECP384R1() if curve is None else curve
    return ec.generate_private_key(
        curve=curve,
        backend=cryptography_default_backend
        )


def generate_dsa_private_key(key_size=1024):
    """
    Generate DSA private key.

    Args:
        key_size (int): Key size of DSA key.

    Return:
        ec.DSAPrivateKey
    """
    return dsa.generate_private_key(
        key_size=key_size,
        backend=cryptography_default_backend
        )


def sign_cert_builder(cert_builder, private_key, alg=None):
    """
    Create certificate from CertificateBuilder and sign with provided key and
    algorithm.

    Args:
        cert_builder (x509.CertificateBuilder): Certificate configuration that
            should be signed.

    Return:
        x509.Certificate
    """
    alg = alg if alg else hashes.SHA256()
    return cert_builder.sign(
        private_key=private_key,
        algorithm=alg,
        backend=cryptography_default_backend
        )


def serialize_key_to_pem(key):
    """
    Serialize private key to OpenSSL format with PEM encoding.

    Args:
        key (rsa.RSAPrivateKey, ec.EllipticCurvePrivateKey): Key to serialize

    Returns:
        PEM text representing serialized key.
    """
    return key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption()
        ).decode('utf-8')


def generate_valid_root_ca_cert_pem(private_key):
    """
    Helper to create and serialize root CA cert.

    Args:
        private_key (rsa.RSAPrivateKey, ec.EllipticCurvePrivateKey): Key that
            should be used for signing the certificate.

    Return:
        PEM text representing serialized certificate.
    """
    return serialize_cert_to_pem(
        sign_cert_builder(
            ca_cert_builder(
                private_key.public_key(),
            ),
            private_key
            )
        )
