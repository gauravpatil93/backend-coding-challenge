# Copyright 2018 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# [START gae_python37_app]
from flask import Flask
from flask_restful import Resource, Api, request
import json
import pandas as pd
import os
import geopy.distance
from fuzzywuzzy import fuzz
from operator import itemgetter
from voluptuous import Required, All, Length, Range, Schema, MultipleInvalid, Invalid, Coerce

# If `entrypoint` is not defined in app.yaml, App Engine will look for an app
# called `app` in `main.py`.
app = Flask(__name__)
api = Api(app)
APP_ROOT = os.path.dirname(os.path.abspath(__file__))


@app.route('/')
def hello():
    """Return a friendly HTTP greeting."""
    return 'Hello World!'


class Suggestions(Resource):
    def fips_mapping(self, fips_code):
        fips_map = {
            "01": "AB",
            "02": "BC",
            "03": "MB",
            "04": "NB",
            "05": "NL",
            "07": "NS",
            "08": "ON",
            "09": "PE",
            "10": "QC",
            "11": "SK",
            "12": "YT",
            "13": "NT",
            "14": "NU"
        }
        return fips_map[fips_code]

    def isascii(self, s):
        """
        The scoring function takes the following argument
        `q`: Unicode

        Function returns True if string containes only
        ascii characters and returns False if the string
        containes non-ascii characters
        """
        return len(s) == len(s.encode())

    def get_fuzzy_score(self, q, name, alt_names):
        """
        The scoring function takes the following arguments
        `q`: String (ascii) - the query string
        `name`: String (ascii) - the name of the city
        `alt_names`: Unicode - the comma seperated alternate names

        The function uses the concept of Fuzzy String Matching to generate
        a similarity score by comparing q with the name and all the alt_names.

        fuzzywuzzy's - `token set approach` - example

        we tokenize both strings, but instead of immediately
        sorting and comparing, we split the tokens into two
        groups: intersection and remainder. We use those
        sets to build up a comparison string.

        s1 = "mariners vs angels"
        s2 = "los angeles angels of anaheim at seattle mariners"

        the set method allows us to detect that “angels” and “mariners”
        are common to both strings, and separate those out
        (the set intersection). Now we construct and compare strings
        of the following form

        t0 = [SORTED_INTERSECTION]
        t1 = [SORTED_INTERSECTION] + [SORTED_REST_OF_STRING1]
        t2 = [SORTED_INTERSECTION] + [SORTED_REST_OF_STRING2]

        And then compare each pair.

        t0 = "angels mariners"
        t1 = "angels mariners vs"
        t2 = "angels mariners anaheim angeles at los of seattle"
        fuzz.ratio(t0, t1) ⇒ 90
        fuzz.ratio(t0, t2) ⇒ 46
        fuzz.ratio(t1, t2) ⇒ 50

        The intuition here is that because the SORTED_INTERSECTION
        component is always exactly the same, the scores increase
        when (a) that makes up a larger percentage of the full string,
        and (b) the string remainders are more similar.
        """

        current_score = fuzz.token_set_ratio(q, name.replace(" ", ""))

        if alt_names != "":
            for alt_name in alt_names.split(","):
                if self.isascii(alt_name):
                    score = fuzz.token_set_ratio(q, alt_name.replace(" ", ""))
                    if score > current_score:
                        pass
                        current_score = score
        return current_score/100 if current_score > 0 else 0

    def get(self):
        # Arguments
        args = request.args.to_dict()

        schema = Schema({
            Required('q'): All(str, Length(min=1)),
            'latitude': All(Coerce(float), Range(min=-90.00, max=90.00)),
            'longitude': All(Coerce(float), Range(min=-180.00, max=180.00))
        })

        try:
            schema(args)
        except Invalid as e:
            return str(e)
        except MultipleInvalid as e:
            return str(e)

        # Response object
        response = {
            "suggestions": []
        }

        if args:

            df = pd.read_table(os.path.join(APP_ROOT, "data", "cities_canada-usa.tsv"))

            ids = df['id'].tolist()

            q = args["q"].lower()

            for rid in ids:
                row = df.loc[df['id'] == rid]

                name = ""
                alt_names = ""

                # continue if there the row does not contain a
                # name and any alternate names
                if pd.isna(row["ascii"].values[0]) and pd.isna(row["alt_name"].values[0]):
                    continue

                # If the ascii value is not none
                if not pd.isna(row["ascii"].values[0]):
                    name = row["ascii"].values[0].lower()

                # If the alt_name value is not none
                if not pd.isna(row["alt_name"].values[0]):
                    alt_names = row["alt_name"].values[0].lower()

                score = self.get_fuzzy_score(q, name, alt_names)

                if score > 0.7:
                    if row["admin1"].values[0].isdigit():
                        # Canada
                        suffix = self.fips_mapping(row["admin1"].values[0]) + ", Canada"
                    else:
                        # USA
                        suffix = row["admin1"].values[0] + ", USA"

                    if "latitude" in args and "longitude" in args:
                        response["suggestions"].append({
                            "name": name.title() + ", " + suffix,
                            "latitude": row["lat"].values[0],
                            "longitude": row["long"].values[0],
                            "score": score,
                            "distance": geopy.distance.distance((args["latitude"], args["longitude"]), (row["lat"].values[0], row["long"].values[0])).km
                        })
                    else:
                        response["suggestions"].append({
                            "name": name.title() + ", " + suffix,
                            "latitude": row["lat"].values[0],
                            "longitude": row["long"].values[0],
                            "score": score
                        })

            response["suggestions"] = sorted(response["suggestions"], key=itemgetter('score'), reverse=True)

            return response
        else:
            return response


# Restful resource endpoint
api.add_resource(Suggestions, '/suggestions')

if __name__ == '__main__':
    # This is used when running locally only. When deploying to Google App
    # Engine, a webserver process such as Gunicorn will serve the app. This
    # can be configured by adding an `entrypoint` to app.yaml.
    app.run(host='127.0.0.1', port=8080, debug=True)
# [END gae_python37_app]
