
from flask import make_response, request, jsonify
from google.cloud import datastore
from utils import error

import json
import constants

client = datastore.Client()

pagination_query_limit = 5

class DB_Obj:
    def __init__(self, id=None, key=None, required=[], optional=[]):
        self.key = key
        self.required = required
        self.optional = optional

        if id:
            self.id = id
            self.item, self.code = self.get_item_from_db(id)


    def check_content_valid(self, content, check_required_exist=True):
        if "id" in content:
            return False, "You may not edit the entry id", 405

        # check for required attributes (can be skipped for PATCH operations)
        if check_required_exist:
            missing = []
            for key in self.required:
                if key not in content:
                    missing.append(key)
            if missing:
                return False, f"The request is missing the following required attributes: {missing}", 400

        content_valid, msg, code = self.validate_values(content)
        if not content_valid:
            return False, msg, code

        return True, "", 200

    def create_new(self, content):
        valid, msg, code = self.check_content_valid(content)
        if not valid:
            return error(msg, code)

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
        return True, f"No extra validation checks for {self.key}", 200

    def delete(self):
        if self.code == 404:
            return error(f"No {self.key} object with this id {self.id} exists", 404)

        client.delete(self.item)

        res = make_response("")
        res.headers.set('Content-Type', 'application/json')
        res.status_code = 204
        return res

    def get_all_items(self):
        query = client.query(kind=self.key)
        q_limit = pagination_query_limit
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
            e["self"] = self.get_item_self(e.key.id)
        output = {self.key: results}
        if next_url:
            output["next"] = next_url
        output["total_items"] = len(list(query.fetch()))
        return json.dumps(output), 200

    def put_item(self, id, content):
        # check for required attributes
        valid, msg, code = self.check_content_valid(content)
        if not valid:
            return error(msg, 400)

        obj, code = self.get_item_from_db(id)
        if code != 200:
            return error(f"No {self.key} object with this id {id} exists", 404)

        for key in self.required + self.optional:
            if key in content:
                obj.update({key: content[key]})

        client.put(obj)
        item, code = self.get_item_from_db(obj.key.id)

        res = make_response(item)
        res.headers.set('Content-Type', 'application/json')
        res.status_code = 303
        return res

    def patch_item(self, id, content):
        # check for required attributes
        valid, msg, code = self.check_content_valid(content, check_required_exist=False)
        if not valid:
            return error(msg, 400)

        obj, code = self.get_item_from_db(id)
        if code != 200:
            return error(f"No {self.key} object with this id {id} exists", 404)

        for key in self.required + self.optional:
            if key in content:
                obj.update({key: content[key]})

        client.put(obj)
        item, code = self.get_item_from_db(obj.key.id)

        res = make_response(item)
        res.headers.set('Content-Type', 'application/json')
        res.status_code = 200
        return res
