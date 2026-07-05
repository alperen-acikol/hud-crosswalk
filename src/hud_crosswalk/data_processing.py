#Packages 
import pandas as pd
import numpy as np
from tabulate import tabulate


class DataProcessing:
    def __init__(self):
        pass


    def data_profile(self,df,column):
        '''
        Profiles a ZIP code column for missing values, invalid characters,
        and incorrect character length.

        Parameters
        ----------
        df : pd.DataFrame
            Input dataframe.
        column : str
            Column name to profile. Column is converted to string internally.

        Returns
        -------
        dict
            Dictionary of profile checks and their counts if no issues are found.
        tuple (dict, pd.DataFrame)
            If issues are found, returns a tuple containing:
            - dict: profile summary with counts per check
            - pd.DataFrame: filtered dataframe of problematic rows with flags
            indicating which check each row failed.

        Notes
        -----
        Missing values are counted separately and are excluded from the
        character and length checks.

        Automatically calls data_filter() if any issues are detected.
        Sets self.profiled = True upon completion, which is required
        before data_filter() can be called independently.
    '''
        data_profile_dict = {
            "Total Missing Values": df[column].isna().sum(),
            "Number of ZIP Codes with character lenght below or above 5": None,
            "Number of ZIP Codes with non-numeric characters": None
        }
        num_list = np.arange(0,10).tolist()
        num_list = [str(x) for x in num_list]
        value = df[column].dropna().astype(str)
        checks ={
            'Presence of non-numeric characters':lambda value: any(char not in num_list for char in str(value)), 
            'Character lenght of ZIP Codes should be 5': lambda value: len(value) !=5
            }
        keys = list(data_profile_dict.keys())
        i = 1
        issues_found = False
        for message,check in checks.items():
            invalid = [x for x in value if check(x)]
            if len(invalid)>0:
                issues_found = True
                print(f"Failed Check: {message}")
            data_profile_dict[keys[i]] = len(invalid) 
            i += 1
            
        print(tabulate(data_profile_dict.items(),headers=["Check","Count"]))
        if issues_found:
            print("Issues found = returning profile summary and problematic rows as a DataFrame.")
            filter_df = self.data_filter(df,column)
            return data_profile_dict,filter_df
    
        return data_profile_dict


    def data_filter(self,df,column):
        '''
        Filters a ZIP code column for problematic values and returns a dataframe
        of rows that failed one or more checks.

        Parameters
        ----------
        df : pd.DataFrame
            Input dataframe.
        column : str
            Column name to filter.

        Returns
        -------
        pd.DataFrame
            Dataframe containing only problematic rows with two additional columns:
            - has_non_numeric: True if the value contains non-numeric characters
            - improper_length: True if the value is not 5 characters long
    
        Notes
        -----
        Call data_profile() first to get a summary of issues before filtering.
        Missing values are excluded from the filtering checks and are not
        included in the returned dataframe. They are handled separately in
        data_profile().

        
        '''
        numeric = np.arange(0,10).tolist()
        numeric = [str(x) for x in numeric]
        filtered_df = df[[column]].dropna().copy()

        filtered_df['has_non_numeric'] = filtered_df[column].astype(str).apply(lambda value: any(char not in numeric for char in value))
        filtered_df['improper_lenght'] = filtered_df[column].astype(str).apply(lambda value: len(value) != 5)
        filtered_df = filtered_df[(filtered_df['has_non_numeric'] == True) | (filtered_df['improper_lenght'] == True)]
        return filtered_df
    

    