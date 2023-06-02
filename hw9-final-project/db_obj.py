
from flask import make_response, request
from google.cloud import datastore
from utils import error

import json
import constants

client = datastore.Client()

class DB_Obj:
    def __init__(self, id=None, key=None, required=[], optional=[]):
        self.key = key
        self.required = required
        self.optional = optional

        if id:
            self.item, self.code = self.get_item_from_db(id)


    def create_new(self, content):
        # check for required attributes
        missing = []
        for key in self.required:
            if key not in content:
                missing.append(key)
        if missing:
            return error(f"The request is missing the following required attributes: {missing}", 400)

        content_valid, msg = self.validate_values(content)
        if not content_valid:
            return error(msg, 403)

        obj = datastore.entity.Entity(key=client.key(self.key))
        for key in self.required + self.optional:
            if key in content:
                obj.update({key: content[key]})

        client.put(obj)
        item, code = self.get_item_from_db(obj.key.id)

        res = make_response(item)
        res.headers.set('Content-Type', 'application/json')
        res.status_code = 201
        return res

    def get_item_from_db(self, id):
        item_key = client.key(self.key, int(id))
        item = client.get(key=item_key)
        if not item:
            return error(f"No {self.key} object with this id {id} exists", 404)
        item["id"] = item.key.id
        item["self"] = self.get_item_self(id)
        return item, 200

    def get_item_self(self, id):
        return f"{constants.url_root}/{self.key}/{id}"

    def validate_values(self, content):
        return True, f"No extra validation checks for {self.key}"

    def delete(self, id=None):
        if not self.item:
            if not id:
                return error("Missing required id for delete", 404)
            self.item, self.code = self.get_item_from_db(id)
            if not self.item:
                return error(f"{self.key} with id {id} not found", 404)

        client.delete(self.item)

        res = make_response("")
        res.headers.set('Content-Type', 'application/json')
        res.status_code = 204
        return res

    def get_all_items(self):
        query = client.query(kind=self.key)
        q_limit = 5 #  int(request.args.get('limit', '5'))
        q_offset = int(request.args.get('offset', '0'))
        g_iterator = query.fetch(limit=q_limit, offset=q_offset)
        pages = g_iterator.pages
        results = list(next(pages))
        if g_iterator.next_page_token:
            next_offset = q_offset + q_limit
            next_url = request.base_url + "?offset=" + str(next_offset) # + "?limit=" + str(q_limit)
        else:
            next_url = None
        for e in results:
            e["id"] = e.key.id
        output = {self.key: results}
        if next_url:
            output["next"] = next_url
        return json.dumps(output), 200