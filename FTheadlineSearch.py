import requests
from urllib.parse import urljoin
import json
import datetime
import pandas as pd
import numpy as np

# example query: FT(api_key).query('euro')

# API-Key obtainable from: https://developer.ft.com/portal
api_key = "<YOUR_API_KEY>"

class FT:
    base_url = 'http://api.ft.com'
    pastTenDays = datetime.datetime.utcnow() - datetime.timedelta(days=10)
    
    def __init__(self, api_key=None):
        if api_key:
            self.api_key = api_key
        else:
            print("************************* \n" +
                  "api_key required \n" +
                  "*************************")
        self.headers = {"X-Api-Key" : api_key}
    
    def query(self, query):
        endpoint = 'content/search/v1?apiKey=' + self.api_key   
        r = requests.post(url = urljoin(self.base_url, endpoint),
                          headers = self.headers, data=self.queryBodyBuilder(queryString=query))
        try:
            r.raise_for_status()
            print("Reponse status code: " + str(r.status_code))
            response = json.loads(r.text)
            self.responseTodf(response)
            return print("DONE!")
        except requests.exceptions.HTTPError:
            print("Reponse status code: " + str(r.status_code))
            raise
    
    # query is set to return past 10 day headlines
    # max number of results returned is by default 100
    # results set to sort by descending order of intial publish datetime...
    # ...remove "sortOrder" & "sortField" for FT default to sort in order of relevancy
    # see https://developer.ft.com/portal/docs-quick-start-guides-headline-licence for details
    def queryBodyBuilder(self, queryString, fromDateTime=pastTenDays, maxResults=100):
        body = json.dumps(
        {
            "queryString": queryString + " AND " + "lastPublishDateTime:>"
            + fromDateTime.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "queryContext": {
            "curations": [
                "ARTICLES",
                "BLOGS",
                "PAGES",
                "PODCASTS",
                "VIDEOS"]
            },
            "resultContext" : {
                 "maxResults": int(maxResults),
                 "aspects" :["title","lifecycle","location","summary","editorial"],
                 "sortOrder" : "DESC",
                 "sortField" : "initialPublishDateTime"
            }
        })
        return body
    
    def responseTodf(self, response):
    # convert json response to DataFrame and save as csv
        try:
            results = response['results'][0]['results']
            resultsDF = pd.DataFrame()
            print("Saving response to CSV...")
            for i in range(len(results)):
                result_title = results[i]['title']['title']
                excerpt = results[i]['summary']['excerpt']
                try:
                    subheading = results[i]['editorial']['subheading']
                except KeyError:
                    subheading = np.nan
                try:
                    by = results[i]['editorial']['byline']
                except KeyError:
                    subheading = np.nan
                initialPublishDate = datetime.datetime.strptime(results[i]['lifecycle']['initialPublishDateTime'],
                                                                "%Y-%m-%dT%H:%M:%SZ")
                lastPublishDate = datetime.datetime.strptime(results[i]['lifecycle']['lastPublishDateTime'],
                                                             "%Y-%m-%dT%H:%M:%SZ")
                modelVersion = results[i]['modelVersion']
                articleID = results[i]['id']
                URI = results[i]['location']['uri']
                aspectSet = results[i]['aspectSet']
                apiURL = results[i]['apiUrl']
                tempDF = pd.DataFrame([[result_title, excerpt, subheading,by,initialPublishDate,
                                        lastPublishDate, modelVersion, articleID, URI, aspectSet, apiURL
                                        ]],columns=['title', 'excerpt', 'subheading', 'by',
                                  'initial_publish_date', 'last_publish_date', 'modelVersion',
                                  'id', 'URI', 'aspectSet', 'apiURL'])
                resultsDF = resultsDF.append(tempDF, ignore_index=True)
                print ("------------------- \n" +
                       "saving results %d" % (i+1))
            resultsDF.to_csv('./FTheadlineResults.csv', index=False)
        except KeyError:
            print("No results found!")
        return None