import tornado.web
import tornado.log
import tornado.options
import logging
import json
import time
import os
import json
import re
import tornado.httpclient

class App(tornado.web.Application):

    def __init__(self, handlers, **kwargs):
        super().__init__(handlers, **kwargs)

class BaseHandler(tornado.web.RequestHandler):
    def write_json(self, obj, status_code=200):
        self.set_header("Access-Control-Allow-Origin", '*')
        self.set_header("Access-Control-Allow-Headers", 'Content-Type')
        self.set_header('Access-Control-Allow-Methods', 'GET')
        self.set_header('Access-Control-Allow-Credentials', 'None')
        self.set_header("Content-Type", "application/json")
        self.set_status(status_code)
        self.write(json.dumps(obj))

# /public-api/listings
class ListingsHandler(BaseHandler):
    @tornado.gen.coroutine
    def get(self):
         # Parsing pagination params
        page_num = self.get_argument("page_num", 1)
        page_size = self.get_argument("page_size", 10)
        try:
            page_num = int(page_num)
        except:
            logging.exception("Error while parsing page_num: {}".format(page_num))
            self.write_json({"result": False, "errors": "invalid page_num"}, status_code=400)
            return

        try:
            page_size = int(page_size)
        except:
            logging.exception("Error while parsing page_size: {}".format(page_size))
            self.write_json({"result": False, "errors": "invalid page_size"}, status_code=400)
            return

        # Parsing user_id param
        user_id = self.get_argument("user_id", None)
        if user_id is not None:
            try:
                user_id = int(user_id)
            except:
                self.write_json({"result": False, "errors": "invalid user_id"}, status_code=400)
                return

        # Build up the queryString
        queryString = '?page_num={0}&page_size={1}'.format(page_num, page_size)
        userQuery = ""

        if user_id is not None:
            userQuery = 'user_id={0}'.format(user_id)
            queryString += userQuery

        http_client = tornado.httpclient.AsyncHTTPClient()

        try:
            # build up the listings
            listingResponse = yield http_client.fetch("https://listing99.herokuapp.com/listings"+ queryString)
            listingJson = json.loads(listingResponse.body)
            listingsResult = listingJson["listings"]

            # get corresponding users
            userResponse = yield http_client.fetch("https://users99.herokuapp.com/users?" + userQuery)
            userJson = json.loads(userResponse.body)
            usersResult = userJson["users"]

            # adds user object for each listing
            for listing in listingsResult:
                userRef = listing["user_id"]
                for user in usersResult:
                    if user["id"] == userRef:
                        listing["user"] = user
                        listing.pop("user_id")

            self.write_json({"result":True, "listings": listingsResult})
            
        except tornado.httpclient.HTTPError as e:
            print(e)
        except Exception as e:
            print(e)

    @tornado.gen.coroutine
    def post(self):
        # Collecting required params
        self.args = json.loads(self.request.body)
        user_id = self.args["user_id"]
        listing_type = self.args["listing_type"]
        price = self.args["price"]

        # Validating inputs
        errors = []
        user_id_val = self._validate_user_id(user_id, errors)
        listing_type_val = self._validate_listing_type(listing_type, errors)
        price_val = self._validate_price(price, errors)

        # End if we have any validation errors
        if len(errors) > 0:
            self.write_json({"result": False, "errors": errors}, status_code=400)
            return

        queryString = "?user_id={0}&listing_type={1}&price={2}".format(user_id_val, listing_type_val, price_val)

        headers={
            "Access-Control-Allow-Origin": '*',
            "Access-Control-Allow-Headers": 'Content-Type',
            'Access-Control-Allow-Methods': 'POST, GET',
            "Content-Type": "application/json"
        }

        http_client = tornado.httpclient.AsyncHTTPClient()

        try:
            # build up the listings
            listingResponse = yield http_client.fetch("https://listing99.herokuapp.com/listings"+queryString, method="POST", body='', headers=headers, connect_timeout=20.0, request_timeout=20.0)
            listingJson = json.loads(listingResponse.body)
            self.write_json({"listing": listingJson['listing']})
        except tornado.httpclient.HTTPError as e:
            print(e)
        except Exception as e:
            print(e)

    def _validate_user_id(self, user_id, errors):
        try:
            user_id = int(user_id)
            return user_id
        except Exception as e:
            logging.exception("Error while converting user_id to int: {}".format(user_id))
            errors.append("invalid user_id")
            return None

    def _validate_listing_type(self, listing_type, errors):
        if listing_type not in {"rent", "sale"}:
            errors.append("invalid listing_type. Supported values: 'rent', 'sale'")
            return None
        else:
            return listing_type

    def _validate_price(self, price, errors):
        # Convert string to int
        try:
            price = int(price)
        except Exception as e:
            logging.exception("Error while converting price to int: {}".format(price))
            errors.append("invalid price. Must be an integer")
            return None

        if price < 1:
            errors.append("price must be greater than 0")
            return None
        else:
            return price


class UsersHandler(BaseHandler):
   
    @tornado.gen.coroutine
    def post(self):
        self.args = json.loads(self.request.body)
        
        # Collecting required params
        name = self.args["name"]

        errors = []
        name_val = self._validate_name(name, errors)
        name_val = name_val.replace(" ", "%20")
        print(name_val)

        # End if we have any validation errors
        if len(errors) > 0:
            self.write_json({"result": False, "errors": errors}, status_code=400)
            return
        
        queryString = "?name={0}".format(name_val)
        print(queryString)

        headers={
            "Access-Control-Allow-Origin": '*',
            "Access-Control-Allow-Headers": 'Content-Type',
            'Access-Control-Allow-Methods': 'POST, GET',
            "Content-Type": "application/json"
        }

        http_client = tornado.httpclient.AsyncHTTPClient()

        try:
            # build up the listings
            userResponse = yield http_client.fetch("https://users99.herokuapp.com/users"+queryString, method="POST", body='', connect_timeout=20.0, request_timeout=20.0, headers=headers)
            userJson = json.loads(userResponse.body)
            self.write_json({"user": userJson['user']})
        except tornado.httpclient.HTTPError as e:
            print(e)
        except Exception as e:
            print(e)

    def _validate_name(self, name, errors):
    
        # Generic RegEx matcher for name validation
        # https://stackoverflow.com/questions/61690985/python-regular-expression-to-validate-name-with-one-or-more-words
        match = re.match(r"^[\-'a-zA-Z ]+$", name)
        if match:
            return name
        else:
            logging.exception("Error while parsing: {}".format(name))
            errors.append("invalid name sequence")
            return None

# /listings/ping
class PingHandler(tornado.web.RequestHandler):
    @tornado.gen.coroutine
    def get(self):
        self.write("pong!")

def make_app(options):
    return App([
        (r"/public-api/ping", PingHandler),
        (r"/public-api/listings", ListingsHandler),
        (r"/public-api/users", UsersHandler)
    ], debug=options.debug)

if __name__ == "__main__":
    # Define settings/options for the web app
    # Specify the port number to start the web app on (default value is port 6000)
    tornado.options.define("port", default=6000)
    # Specify whether the app should run in debug mode
    # Debug mode restarts the app automatically on file changes
    tornado.options.define("debug", default=True)

    # Read settings/options from command line
    tornado.options.parse_command_line()

    # Access the settings defined
    options = tornado.options.options
    
    # Create web app
    app = make_app(options)
    port = int(os.environ.get("PORT", options.port))
    app.listen(port)
    logging.info("Starting user service. PORT: {}, DEBUG: {}".format(port, options.debug))

    # Start event loop
    tornado.ioloop.IOLoop.instance().start()