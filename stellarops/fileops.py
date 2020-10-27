import json
import base64
import os
import getpass
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.fernet import Fernet, InvalidToken


def get_password_from_user():
    print("Private key is encrypted. Please input password.")
    p = getpass.getpass(prompt='Password: ', stream=None)
    return p


def generate_key_from_password(password, salt=None):
    password_encoded = password.encode()  # Convert to type bytes
    if salt is None:
        salt = os.urandom(16)
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
        backend=default_backend()
    )
    key = base64.urlsafe_b64encode(kdf.derive(password_encoded))
    return key, salt


def key_encrypt_with_password(data_string, password):
    if password is None:
        return data_string
    if '$' in data_string:
        salt, data = data_string.split('$')
    else:
        salt = None
        data = data_string
    key, salt = generate_key_from_password(password=password, salt=salt)
    f = Fernet(key)
    data_encoded = data.encode('ascii')
    encrypted_data = f.encrypt(data=data_encoded)
    encrypted_data_string = "{}${}".format(base64.b64encode(salt).decode('ascii'),
                                           base64.b64encode(encrypted_data).decode('ascii'))
    return encrypted_data_string


def key_decrypt_with_password(data_string):
    if '$' in data_string:
        salt, data = data_string.split('$')
        password = get_password_from_user()
        if password is None:
            raise Exception("Password needed, but not provided")
    else:
        return data_string
    key, salt = generate_key_from_password(password=password, salt=base64.b64decode(salt))
    f = Fernet(key)
    data_binary = base64.b64decode(data)
    try:
        decrypted_data = f.decrypt(data_binary)
        return decrypted_data.decode('ascii')
    except InvalidToken:
        raise Exception("Cannot decrypt private key. Perhaps invalid password was provided.")


def write_wallet(wallet_file, private_key, public_key, password=None):
    password = getpass.getpass(prompt="Password for private key encryption (press ENTER for no encryption):")
    if password is None or len(password.strip()) == 0:
        print("Skipping private key encryption.")
        password = None
    f = open(wallet_file, "w")
    json_data = {
        "public_key": public_key,
        "private_key": key_encrypt_with_password(data_string=private_key, password=password)
    }
    f.write(json.dumps(json_data, indent=4))
    f.close()


def load_wallet(wallet_file):
    f = open(wallet_file, mode="r")
    content = f.read()
    json_data = json.loads(content)
    f.close()
    private_key = key_decrypt_with_password(data_string=json_data.get("private_key"))
    public_key = json_data.get("public_key")
    return (private_key, public_key)
