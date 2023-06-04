from child import Child

from google.cloud import datastore

client = datastore.Client()

def test_birthday():
    content = {
        "name": "Dummy Name",
        "birthday": "2022-06-04"
    }

    child = Child().create_new(content)
    # child.delete()

if __name__ == '__main__':
    test_birthday()

