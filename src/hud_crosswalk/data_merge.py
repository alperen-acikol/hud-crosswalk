#Packages
import pandas as pd



class DataMerge:
    def __init__(self, huds_zip='zip', huds_geoid='geoid', huds_res_ratio='res_ratio'):
        '''
        Initializes the DataMerge class with default HUD column names.
        Column names can be overridden if the HUD data has different column names.

        Parameters
        ----------
        huds_zip : str
            Name of the ZIP code column in the HUD crosswalk dataframe.
            Default is 'zip' based on standard HUD column naming.
        huds_geoid : str
            Name of the geoid/FIPS column in the HUD crosswalk dataframe.
            Default is 'geoid' based on standard HUD column naming.
        huds_res_ratio : str
            Name of the residential ratio column in the HUD crosswalk dataframe.
            Default is 'res_ratio' based on standard HUD column naming.

        Examples
        --------
        Default HUD column names:
            dm = DataMerge()

        Custom HUD column names:
            dm = DataMerge(huds_zip='zipcode', huds_geoid='fips', huds_res_ratio='ratio')
        '''
        self.huds_zip = huds_zip
        self.huds_geoid = huds_geoid
        self.huds_res_ratio = huds_res_ratio

    def data_prep(self, df, col) -> pd.DataFrame:
        '''
        Standardizes a ZIP code or geoid column by converting to string,
        stripping whitespace, and zero filling to 5 digits.

        Pandas drops leading zeros when reading numeric columns — for example
        ZIP code 01234 becomes 1234 when read as an integer. This method
        restores leading zeros to ensure correct matching during merges.
        Without this step, 01234 and 1234 would not match as strings even
        though they represent the same ZIP or geoid code.

        Called internally by zip_to_location() on the HUD dataframe and by
        assign_geoid_main_dataframe() on the main dataframe. Can also be
        called directly on any dataframe with a ZIP or geoid column.

        Parameters
        ----------
        df : pd.DataFrame
            Input dataframe — either HUD crosswalk or main dataframe.
        col : str
            Name of the column to standardize.

        Returns
        -------
        pd.DataFrame
            Dataframe with standardized column.
        '''
        df[col] = df[col].astype(str).str.strip().str.zfill(5)
        return df

    def mapping_dict(self, huds_df) -> dict:
        '''
        Creates a dictionary mapping each ZIP code to a list of geoids
        from the HUD crosswalk dataframe.

        A ZIP code can map to multiple counties — this method captures all
        matches as a list rather than a single value. The resulting dictionary
        is used by assign_geoid_main_dataframe() to map geoids onto the main
        dataframe.

        Called internally by zip_to_location(). All inputs should come from
        the HUD crosswalk dataframe, not the main dataframe being merged.
        HUD column names are read from instance attributes set in __init__().

        Parameters
        ----------
        huds_df : pd.DataFrame
            HUD crosswalk dataframe.

        Returns
        -------
        dict
            Dictionary mapping ZIP codes to a list of geoids.
        '''
        col_dict = huds_df.groupby(self.huds_zip)[self.huds_geoid].apply(list).to_dict()
        return col_dict

    def zip_to_location(self, huds_df) -> dict:
        '''
        Prepares HUD crosswalk data and creates a ZIP to geoid mapping dictionary.

        All inputs should come from the HUD crosswalk dataframe.
        The mapping dictionary is returned explicitly — store it and pass it
        to assign_geoid_main_dataframe() to ensure the correct mapping is used
        for each workflow. Using instance attributes instead risks silent failures
        when multiple workflows are run from the same instance.

        HUD column names are read from instance attributes set in __init__().

        Parameters
        ----------
        huds_df : pd.DataFrame
            HUD crosswalk dataframe. Not the main dataframe being merged.

        Returns
        -------
        dict
            Dictionary mapping ZIP codes to a list of geoids.
            Store this and pass it explicitly to assign_geoid_main_dataframe().
        '''
        prepped_huds = self.data_prep(huds_df, self.huds_geoid)
        col_dict = self.mapping_dict(prepped_huds)
        return col_dict

    def assign_geoid_main_dataframe(self, df, df_zip, col_dict) -> pd.DataFrame | None:
        '''
        Maps geoids from the HUD crosswalk onto the main dataframe by ZIP code.
        ZIP codes in the main dataframe are standardized before mapping.

        This method operates on the main dataframe — not the HUD crosswalk data.
        col_dict must be passed explicitly from the return value of
        zip_to_location() to ensure the correct mapping is used. This avoids
        silent failures where the wrong auxiliary data is used without any
        error being raised.

        ZIP codes are converted to string, stripped of whitespace, and zero
        filled to 5 digits to ensure correct matching — pandas drops leading
        zeros when reading numeric columns, so 1234 becomes 01234 after
        zero fill.

        Parameters
        ----------
        df : pd.DataFrame
            Main dataframe to enrich. Target of the merge, not the HUD data.
        df_zip : str
            Name of the ZIP code column in the main dataframe.
        col_dict : dict
            Mapping dictionary returned by zip_to_location(). Must be passed
            explicitly to ensure correct mapping per workflow.

        Returns
        -------
        pd.DataFrame
            Main dataframe with new geoid_huds column containing matched geoids.
        None
            If col_dict is None.
        '''
        if col_dict is None:
            print("col_dict is None. Pass the return value of zip_to_location().")
            return None

        df = self.data_prep(df, df_zip)
        df['geoid_huds'] = df[df_zip].map(col_dict)
        return df

    def expand_geoid_columns(self, df, geoid_huds) -> pd.DataFrame | None:
        '''
        Expands a column containing lists of geoids into separate columns.
        Each position in the list becomes its own column (geoid_1, geoid_2 etc.).
        Shorter lists are padded with 0 to match the longest list.

        Parameters
        ----------
        df : pd.DataFrame
            Main dataframe containing the geoid list column.
        geoid_huds : str
            Name of the column containing lists of geoids.
            Must be created by assign_geoid_main_dataframe() first.

        Returns
        -------
        pd.DataFrame
            Dataframe with expanded geoid columns.
        None
            If geoid column is not found in the dataframe.
        '''
        if geoid_huds not in df.columns:
            print(f'{geoid_huds} column not found. Run assign_geoid_main_dataframe() first.')
            return None

        # convert the geoid column to a list of lists
        # each row is a list of geoids assigned to that ZIP code
        geoid_list = list(df[geoid_huds])

        # find the longest list — determines how many columns are needed
        max_length = max(len(lst) for lst in geoid_list)

        # pad shorter lists with 0 so every list is the same length
        # e.g. ['51059'] becomes ['51059', 0, 0] if max_length is 3
        geoid_list = [lst + [0] * (max_length - len(lst)) for lst in geoid_list]

        # transpose — rotate the list of lists 90 degrees
        # before: each inner list is a row  [['51059', '51600'], ['51059', 0]]
        # after:  each inner list is a column [['51059', '51059'], ['51600', 0]]
        columns = [[lst[i] for lst in geoid_list] for i in range(max_length)]

        # assign each transposed list as a new column in the dataframe
        # geoid_1 gets the first geoid from each row, geoid_2 the second, and so on
        for i in range(max_length):
            df[f'geoid_{i+1}'] = columns[i]

        return df

    def resolve_multi_county_zip(self, huds_df) -> tuple[dict, dict]:
        '''
        Resolves ZIP codes that cover multiple counties by selecting the county
        with the highest residential address ratio.

        Builds a nested dictionary of ZIP codes, geoids, and residential ratios
        from the HUD crosswalk data. For each ZIP code that maps to multiple
        counties, selects the geoid with the highest residential ratio as the
        most representative county for that ZIP code.

        HUD column names are read from instance attributes set in __init__().

        Parameters
        ----------
        huds_df : pd.DataFrame
            HUD crosswalk dataframe.

        Returns
        -------
        tuple (dict, dict)
            highest_values : dict
                Dictionary mapping each ZIP code to the geoid with the
                highest residential ratio. Used for mapping onto the main
                dataframe.
            zipcode_nested_dict : dict
                Full nested dictionary of ZIP codes, geoids, and ratios.
                Returned for reference and inspection purposes.
        '''
        highest_values = {}
        zipcode_nested_dict = huds_df.groupby(self.huds_zip).apply(
            lambda x: dict(zip(x[self.huds_geoid], x[self.huds_res_ratio]))
        ).to_dict()

        for zipcode, geoid in zipcode_nested_dict.items():
            max_geoid = max(geoid, key=geoid.get)
            highest_values[zipcode] = max_geoid

        return highest_values, zipcode_nested_dict

    def run(self, df, huds_df, df_zip) -> pd.DataFrame | None:
        '''
        Runs the full ZIP to geoid mapping pipeline in the correct order.
        Calls zip_to_location(), assign_geoid_main_dataframe(),
        expand_geoid_columns(), and resolve_multi_county_zip() internally.

        HUD column names are read from instance attributes set in __init__().
        Main dataframe ZIP column must be passed explicitly.

        Parameters
        ----------
        df : pd.DataFrame
            Main dataframe to enrich.
        huds_df : pd.DataFrame
            HUD crosswalk dataframe.
        df_zip : str
            Name of the ZIP code column in the main dataframe.

        Returns
        -------
        pd.DataFrame
            Main dataframe with geoid columns expanded, assigned, and
            resolved for ZIP codes covering multiple counties.
        None
            If any step fails.
        '''
        # build mapping dictionary from HUD data
        col_dict = self.zip_to_location(huds_df)

        # map geoids onto main dataframe
        df = self.assign_geoid_main_dataframe(df, df_zip, col_dict)
        if df is None:
            return None

        # expand geoid lists into separate columns
        df = self.expand_geoid_columns(df, 'geoid_huds')
        if df is None:
            return None

        # resolve multi county ZIPs to single best geoid by residential ratio
        highest_values, _ = self.resolve_multi_county_zip(huds_df)
        df['assigned_geoid'] = df[df_zip].map(highest_values)

        return df


