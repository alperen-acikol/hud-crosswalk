#Packages
import os 
import sys
import pandas as pd
import requests 


class DataLoad:
    def __init__(self):
        pass


## Data Load Function
    def data_load(self, path, filename) -> pd.DataFrame | None:
        '''
        Loads a csv or xlsx file from a given path and filename.
        Other formats are not supported.

        Parameters
        ----------
        path : str
            Folder path containing the file.
        filename : str
            Filename without the extension. Partial names are supported —
            the function will match any file containing the provided string. 

        Returns
        -------
        pd.DataFrame
            Loaded dataframe if file is found and format is supported.
        None
            If file is not found or format is not supported.
        '''
        file_list = os.listdir(path)
        matches = [x for x in file_list if filename in x]

        if matches:
            file = matches[0]
            full_path = os.path.join(path, file)

            if file.endswith('.csv'):
                df = pd.read_csv(full_path)
            elif file.endswith('.xlsx'):
                df = pd.read_excel(full_path)
            else:
                print('File format not supported')
                return None
            return df
        else:
            print(f'{filename} does not exist in {path}')
            return None

 

## HUDS API Global Parameter Function
    def huds_api(self,api_token):
        '''
        Prompts user to input their HUD API token and stores it as an instance attribute.
        Can be accessed by other methods via self.api without needing to pass it explicitly.
        '''
        self.api = api_token

## HUDS URL Modifier Function
    def huds_url_modifier(self,type,query='All',year=None,quarter=None):
        '''
        Builds the query parameter dictionary for the HUD API request.

        Parameters
        ----------
        crosswalk_type : int
            Number between 1 and 12, defines the type of crosswalk data.
        query : str
            Default is 'All'. ZIP/tract/county/CBSA/state code, etc.
        year : int, optional
            Year of the data. Defaults to latest if None.
        quarter : int, optional
            Quarter (1-4). Defaults to latest if None.

        See: https://www.huduser.gov/portal/dataset/uspszip-api.html
        '''
        url_params = {
            "crosswalk_type":type,
            "query":query,
            "year": year,
            "quarter":quarter
            }
        return url_params

## HUDS API Call Function
    def api_call(self,api_token,url_params):
        '''
        Makes a GET request to the HUD USPS Crosswalk API and returns the response data.

        Parameters
        ----------
        url_params : dict
            Dictionary of query parameters built by huds_url_modifier().
            Contains type, query, year, and quarter keys.

        Notes
        -----
            Requires huds_api() to be called first to set self.api.
            Requires huds_url_modifier() to be called first to build url_params.

        Returns
        -------
            pd.DataFrame
            DataFrame of crosswalk results if successful.
            Prints an error message and returns None if the request fails.
        '''
        response_codes = {
            200 : 'Request was successful',
            400 : 'An invalid value was specified for one of the query parameters in the request URI',
            401 : 'Authentication failure',
            403 : 'Not allowed to access this dataset API because you have not registered for it',
            404 : 'No data found using value you entered',
            405 : 'Unsupported method, only GET is supported',
            406 : 'Unsupported Accept Header value, must be application/json',
            500 : 'Internal server error occurred'
            }
        
        huds_url = "https://www.huduser.gov/hudapi/public/usps"
        headers ={"Authorization": f"Bearer {api_token}"}
        response = requests.get(huds_url,headers=headers,params=url_params)
        if response.status_code !=200:
            print(f"{response.status_code}:{response_codes.get(response.status_code,f'Unknown status code: {response.status_code}')}")
        else:
            huds_crosswalk_data = pd.DataFrame(response.json()["data"]["results"])
        return huds_crosswalk_data


