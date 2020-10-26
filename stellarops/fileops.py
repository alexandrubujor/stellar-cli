import json


def write_wallet(wallet_file, private_key, public_key):
    f = open(wallet_file, "w")
    json_data = {
        "public_key": public_key,
        "private_key": private_key
    }
    f.write(json.dumps(json_data, indent=4))
    f.close()


def load_wallet(wallet_file):
    f = open(wallet_file, mode="r")
    content = f.read()
    json_data = json.loads(content)
    f.close()
    private_key = json_data.get("private_key")
    public_key = json_data.get("public_key")
    return (private_key, public_key)