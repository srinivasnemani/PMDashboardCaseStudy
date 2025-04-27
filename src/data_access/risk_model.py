from sqlalchemy import text

from src.data_access.crud_util import DataAccessUtil
from src.data_access.schemas import RiskModel
from src.data_access.sqllite_db_manager import TableNames


class RiskModelDataUtil:

    @staticmethod
    def _fetch_factor_exposures(date_val):
        tbl_name = TableNames.RISK_FACTOR_EXPOSURES.value

        industry_query = f"""
        SELECT ie.date, ie.ticker, ie.factor, ie.exposure
        FROM {tbl_name} ie
        WHERE date(ie.date) = date('{date_val}')
        """
        query_string = text(industry_query)
        factor_exposures = DataAccessUtil.fetch_data_from_db(query_string)

        pivoted_df = factor_exposures.pivot_table(
            index=['date', 'ticker'],
            columns='factor',
            values='exposure',
            aggfunc='first'  # In case there are duplicates
        ).reset_index()
        return pivoted_df

    @staticmethod
    def _fetch_factor_covariance(date_val):
        tbl_name = TableNames.RISK_FACTOR_COVARIANCE.value

        covariance_query = f"""
        SELECT fc.date, fc.factor_1, fc.factor_2, fc.covariance
        FROM {tbl_name} fc
        WHERE date(fc.date) = date('{date_val}')
        """
        query_string = text(covariance_query)
        factor_covariance = DataAccessUtil.fetch_data_from_db(query_string)
        factor_covariance_pivoted = factor_covariance.pivot(index='factor_1', columns='factor_2', values='covariance')
        return factor_covariance_pivoted

    @staticmethod
    def _fetch_sp_risk_residuals(date_val):
        tbl_name = TableNames.RISK_SPRISK_RESIDUALS.value

        sprisk_residuals_query = f"""
        SELECT sr.date, sr.ticker, sr.specific_risk, sr.residual
        FROM {tbl_name} sr
        WHERE date(sr.date) = date('{date_val}')
        """
        query_string = text(sprisk_residuals_query)
        sprisk_residuals_df = DataAccessUtil.fetch_data_from_db(query_string)

        return sprisk_residuals_df

    def fetch_risk_model(date_val):
        factor_exposures = RiskModelDataUtil._fetch_factor_exposures(date_val)
        factor_covar = RiskModelDataUtil._fetch_factor_covariance(date_val)
        sp_risk = RiskModelDataUtil._fetch_sp_risk_residuals(date_val)
        list_factors = list(factor_covar.columns.unique())
        risk_model_obj = RiskModel(date_val, list_factors, factor_exposures, factor_covar, sp_risk)
        return risk_model_obj


if __name__ == "__main__":
    # For testing.
    date_val = "2024-01-12"
    v1 = RiskModelDataUtil.fetch_risk_model(date_val)
    print(v1)
