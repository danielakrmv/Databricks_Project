from datetime import datetime

from databricks.src.uapc_aiacad.transformations.get_most_purchased_and_less_purchased_articles_per_unit_of_measure \
    import *
from decimal import Decimal
import unittest
from pyspark.sql import SparkSession
from pyspark import Row
from pyspark.sql.types import (StructField, StringType, IntegerType, TimestampType, LongType,
                               StructType, DecimalType)


df_sales_schema = Row("bon_id", "bon_zeile", "kl-art_id", "menge", "einh_id", "aktion_fg", "k_bon_beginn")

filtered_df_sales = Row("kl-art_id", "menge", "einh_id", "aktion_fg", "kl-art_bez", "wug_bez", "art_bez")

final_df_articles_per_unit = ("article_id", "quantity_per_unit", "action_flag", "names_of_articles_gm",
                              "group_names", "names_of_articles_bg")

final_df_articles_per_weight = ("article_id", "quantity_per_weight_kg", "action_flag", "names_of_articles_gm",
                                "group_names", "names_of_articles_bg")


def check_sales_schema(testclass, dataframe_sales):
    testclass.assertTrue(StructField("bon_id", StringType(), True) in dataframe_sales.schema)
    testclass.assertTrue(StructField("bon_zeile", LongType(), False) in dataframe_sales.schema)
    testclass.assertTrue(StructField("menge", IntegerType(), False) in dataframe_sales.schema)


class TestFindingArticlesPerUnitAndWeight(unittest.TestCase):

    def setUp(self):
        # Create local spark session for component testing
        self._mySpark = SparkSession.builder.master("local[2]").appName("unittest").getOrCreate()
        self._mySpark.conf.set("spark.sql.session.timeZone", "UTC")

        self.period_in_weeks = 5

        self.timestamp_08 = datetime.strptime("2022-10-08 08:47:57", '%Y-%m-%d %H:%M:%S')
        self.timestamp_10 = datetime.strptime("2022-10-11 10:50:57", '%Y-%m-%d %H:%M:%S')
        self.timestamp_13 = datetime.strptime("2022-10-06 13:59:03", '%Y-%m-%d %H:%M:%S')
        self.timestamp_17 = datetime.strptime("2022-10-20 17:53:16", '%Y-%m-%d %H:%M:%S')
        self.timestamp_invalid_2022 = datetime.strptime("2022-08-11 09:12:43", '%Y-%m-%d %H:%M:%S')
        self.timestamp_invalid_2014 = datetime.strptime("2014-10-12 12:12:23", '%Y-%m-%d %H:%M:%S')

        schema_sales = StructType([
            StructField("bon_id", StringType(), True),
            StructField("bon_zeile", IntegerType(), True),
            StructField("kl_art_id", IntegerType(), True),
            StructField("menge", DecimalType(), True),
            StructField("einh_id", StringType(), True),
            StructField("aktion_fg", IntegerType(), True),
            StructField("k_bon_beginn", TimestampType(), True),
        ])

        schema_filtered_sales_with_names_articles = StructType([
            StructField("kl_art_id", IntegerType(), True),
            StructField("menge", DecimalType(18, 3), True),
            StructField("einh_id", StringType(), True),
            StructField("aktion_fg", IntegerType(), True),
            StructField("kl_art_bez", StringType(), True),
            StructField("wug_bez", StringType(), True),
            StructField("art_bez", StringType(), True),
        ])

        df_sales = (
            [("valid_bon_id_1", 1, 2500199, Decimal(1.000), "ST", 1, self.timestamp_08),
             ("valid_bon_id_1", 2, 10468, Decimal(3.000), "ST", 0, self.timestamp_08),
             ("valid_bon_id_1", 3, 10468, Decimal(34.567), "KG", 1, self.timestamp_08),
             ("valid_bon_id_1", 4, 2800444, Decimal(3.213), "KG", 1, self.timestamp_08),
             ("missing_rows_bon_id", 1, 28768, Decimal(0.340), "KG", 0, self.timestamp_10),
             ("missing_rows_bon_id", 3, 43973, Decimal(1.000), "ST", 1, self.timestamp_10),
             ("missing_rows_bon_id", 4, 5103165, Decimal(6.000), "ST", 1, self.timestamp_10),
             ("missing_rows_bon_id", 6, 5103165, Decimal(1.000), "ST", 0, self.timestamp_10),
             ("bon_id_with_none", 1, 9702481, Decimal(5.213), "KG", 1, self.timestamp_13),
             ("bon_id_with_none", None, 9702481, Decimal(2.000), "ST", 1, self.timestamp_13),
             ("bon_id_with_none", 2, 802481, Decimal(1.000), "ST", 0, self.timestamp_13),
             ("invalid_date_bon_id_1", 13, 9700028, Decimal(2.206), "KG", 1, self.timestamp_invalid_2022),
             ("invalid_date_bon_id_2", 2,  62248, Decimal(12.000), "ST", 0, self.timestamp_invalid_2014),
             ("valid_bon_id_2", 1, 107572, Decimal(1.000), "ST", 1, self.timestamp_17),
             ("valid_bon_id_2", 2, 1000431, Decimal(3.000), "ST", 0, self.timestamp_17),
             ("valid_bon_id_2", 3, 1000431, Decimal(5.567), "KG", 1, self.timestamp_17),
             ("valid_bon_id_2", 4, 5103165, Decimal(1.213), "KG", 1, self.timestamp_17),
             ("valid_bon_id_2", 5, 75725, Decimal(2.000), "ST", 1, self.timestamp_17),
             ("valid_bon_id_2", 6, 9700011, Decimal(1.000), "ST", 1, self.timestamp_17),
            ]
        )

        df_filtered_sales_with_names_articles = ([
            (10468, Decimal(1.000), "ST", 1, "Somersby Birnencider 0,33l", "Cider", "Somersby сайдер круша 4,5% 0,33л бут."),
            (13913, Decimal(3.000), "ST", 0, "Amelia Travel Wet Wipes 15 pce.", "Kosmetiktuecher", "Amelia мокри кърпички антибакт. 15 бр"),
            (13913, Decimal(1.000), "ST", 0, "Amelia Travel Wet Wipes 15 pce.", "Kosmetiktuecher", "Amelia мокри кърпички антибакт. 15 бр"),
            (13913, Decimal(2.000), "ST", 0, "Amelia Travel Wet Wipes 15 pce.", "Kosmetiktuecher", "Amelia мокри кърпички антибакт. 15 бр"),
            (15899, Decimal(1.000), "ST", 1, "Cappy Pulpy Orange 1 l", "Orangensaft", "Cappy Pulpy портокал 7% 1л PET"),
            (15899, Decimal(1.000), "ST", 1, "Cappy Pulpy Orange 1 l", "Orangensaft", "Cappy Pulpy портокал 7% 1л PET"),
            (35090, Decimal(3.512), "KG", 0, "Mackrele ganze 400-600 gefrorene, kg", "Ganze Fische salzw.", "Скумрия едра замразена, кг"),
            (35090, Decimal(1.114), "KG", 0, "Mackrele ganze 400-600 gefrorene, kg", "Ganze Fische salzw.", "Скумрия едра замразена, кг"),
        ])

        self.test_df_sales = self._mySpark.createDataFrame(df_sales, schema_sales)
        self.test_df_filtered_sales_with_names_articles = self._mySpark.createDataFrame(df_filtered_sales_with_names_articles,
                                                                                       schema_filtered_sales_with_names_articles)

    def test_check_sales_schema(self):

        self.assertTrue(StructField("bon_id", StringType(), True) in self.test_df_sales.schema)
        self.assertTrue(StructField("bon_zeile", IntegerType(), True) in self.test_df_sales.schema)
        self.assertTrue(StructField("kl_art_id", IntegerType(), True) in self.test_df_sales.schema)
        self.assertTrue(StructField("menge", DecimalType(), True) in self.test_df_sales.schema)
        self.assertTrue(StructField("einh_id", StringType(), True) in self.test_df_sales.schema)
        self.assertTrue(StructField("aktion_fg", IntegerType(), True) in self.test_df_sales.schema)
        self.assertTrue(StructField("k_bon_beginn", TimestampType(), True) in self.test_df_sales.schema)

    def test_chek_if_format_type_is_not_valid__expect_raises(self):
        invalid_format = "avro"

        with self.assertRaises(ValueError) as error:
            Validator.raise_if_format_type_is_not_valid(invalid_format)

        self.assertEqual("Invalid format! The dataset you want to read is format 'delta'", str(error.exception))


    def test_selecting_columns_from_dataFrame(self):
        expected_columns = ["bon_id", "bon_zeile", "kl_art_id", "menge", "einh_id", "aktion_fg", "k_bon_beginn"]
        actual = select_columns(self.test_df_sales, "bon_id", "bon_zeile", "kl_art_id", "menge", "einh_id", "aktion_fg",
                                "k_bon_beginn").columns
        self.assertEqual(actual, expected_columns)

    def test_take_date_weeks_before_current_date_when_weeks_are_negative_number__expected_yesterday(self):
        expected = datetime.now().date()
        actual = take_date_weeks_before_current_date(weeks_period=-10)
        self.assertEqual(actual, expected)

    def test_take_date_weeks_before_current_date_when_weeks_are_correct_number(self):
        my_weeks_period = 5
        expected = datetime.now().date() - timedelta(weeks=my_weeks_period)
        actual = take_date_weeks_before_current_date(weeks_period=5)
        self.assertEqual(actual, expected)

    def test_get_needed_data_for_curr_period_when_df_is_not_none(self):

        old_df_row_count = self.test_df_sales.count()
        new_df_row_count = get_needed_data_for_curr_period(self.test_df_sales, "k_bon_beginn",
                                                           self.period_in_weeks).count()

        self.assertEqual(old_df_row_count, 19)
        self.assertEqual(new_df_row_count, 17)

    def test_get_needed_data_for_curr_period_when_df_is_none(self):
        self.period_in_weeks = 5
        self.test_df_sales = self.test_df_sales.show()

        with self.assertRaises(AttributeError) as error:
            get_needed_data_for_curr_period(self.test_df_sales, "k_bon_beginn",
                                            self.period_in_weeks).count()
        self.assertEqual("NoneType object has no attribute 'where'!", str(error.exception))

    def test_get_correct_bon_id(self):
        old_df_row_count = self.test_df_sales.count()
        new_df_row_count_with_only_correct_bon_ids = get_correct_bon_id(self.test_df_sales, "bon_id").count()

        expected_max_bon_zeile_first_valid_id = 4
        expected_max_bon_zeile_second_valid_id = 6
        expected_count_bon_id_first_valid_id = 4
        expected_count_bon_id_second_valid_id = 6
        expected_count_bon_zeile_first_valid_id = 4
        expected_count_bon_zeile_second_valid_id = 6

        df_with_correct_bon_ids = get_correct_bon_id(self.test_df_sales, "bon_id")

        self.assertEqual(old_df_row_count, 19)
        self.assertEqual(new_df_row_count_with_only_correct_bon_ids, 2)

        actual_max_bon_zeile_first_bon_id = df_with_correct_bon_ids.select("max_bon_zeile").collect()[0][0]
        actual_max_bon_zeile_second_bon_id = df_with_correct_bon_ids.select("max_bon_zeile").collect()[1][0]
        actual_count_bon_id_first_bon_id = df_with_correct_bon_ids.select("count_bon_id").collect()[0][0]
        actual_count_bon_id_second_bon_id = df_with_correct_bon_ids.select("count_bon_id").collect()[1][0]
        actual_count_bon_zeile_first_bon_id = df_with_correct_bon_ids.select("count_bon_zeile").collect()[0][0]
        actual_count_bon_zeile_second_bon_id = df_with_correct_bon_ids.select("count_bon_zeile").collect()[1][0]

        self.assertEqual(actual_max_bon_zeile_first_bon_id, expected_max_bon_zeile_first_valid_id)
        self.assertEqual(actual_max_bon_zeile_second_bon_id, expected_max_bon_zeile_second_valid_id)
        self.assertEqual(actual_count_bon_id_first_bon_id, expected_count_bon_id_first_valid_id)
        self.assertEqual(actual_count_bon_id_second_bon_id, expected_count_bon_id_second_valid_id)
        self.assertEqual(actual_count_bon_zeile_first_bon_id, expected_count_bon_zeile_first_valid_id)
        self.assertEqual(actual_count_bon_zeile_second_bon_id, expected_count_bon_zeile_second_valid_id)

    def test_get_data_per_unit_of_measure_if_measure_is_not_valid__expect_raises(self):
        test_unit_of_measure = "gr"

        with self.assertRaises(ValueError) as error:
            get_data_per_unit_of_measure(df=self.test_df_filtered_sales_with_names_articles,
                                         column_to_filter="einh_id",
                                         column_to_group_by="kl_art_id",
                                         unit_of_measure=test_unit_of_measure)
            self.assertEqual("Unit of measure can be only 'KG' or 'ST'!", str(error.exception))

    def test_get_data_per_unit_of_measure_if_measure_is_per_unit(self):
        test_unit_of_measure = "ST"

        old_df_row_count = self.test_df_filtered_sales_with_names_articles.count()
        new_df_row_count = get_data_per_unit_of_measure(df=self.test_df_filtered_sales_with_names_articles,
                                                        column_to_filter="einh_id",
                                                        column_to_group_by="kl_art_id",
                                                        unit_of_measure=test_unit_of_measure).count()

        self.assertEqual(old_df_row_count, 8)
        self.assertEqual(new_df_row_count, 3)

        df_per_unit = get_data_per_unit_of_measure(df=self.test_df_filtered_sales_with_names_articles,
                                                   column_to_filter="einh_id",
                                                   column_to_group_by="kl_art_id",
                                                   unit_of_measure=test_unit_of_measure)

        df_per_unit_dict = [res.asDict() for res in df_per_unit.collect()]
        self.assertTrue({"kl_art_id": 10468, "Total Menge per one art_id ST": 1} in df_per_unit_dict)
        self.assertTrue({"kl_art_id": 13913, "Total Menge per one art_id ST": 6} in df_per_unit_dict)
        self.assertTrue({"kl_art_id": 15899, "Total Menge per one art_id ST": 2} in df_per_unit_dict)

    def test_get_data_per_unit_of_measure_if_measure_is_per_weight(self):
        test_unit_of_measure = "KG"

        old_df_row_count = self.test_df_filtered_sales_with_names_articles.count()
        new_df_row_count = get_data_per_unit_of_measure(df=self.test_df_filtered_sales_with_names_articles,
                                                        column_to_filter="einh_id",
                                                        column_to_group_by="kl_art_id",
                                                        unit_of_measure=test_unit_of_measure).count()

        self.assertEqual(old_df_row_count, 8)
        self.assertEqual(new_df_row_count, 1)

        df_per_weight = get_data_per_unit_of_measure(df=self.test_df_filtered_sales_with_names_articles,
                                                     column_to_filter="einh_id",
                                                     column_to_group_by="kl_art_id",
                                                     unit_of_measure=test_unit_of_measure)

        df_per_weight_dict = [res.asDict() for res in df_per_weight.collect()]

        self.assertTrue({"kl_art_id": 35090, "Total Menge per one art_id KG": 4.630000114440918} in df_per_weight_dict)

    def test_joining_tables_with_correct_bon_ids(self):

        old_df_row_count = self.test_df_sales.count()
        expected_joined_table_row_count = 10

        df_sales_for_last_5_weeks = get_needed_data_for_curr_period(df=self.test_df_sales,
                                                                    date_column="k_bon_beginn",
                                                                    period_in_weeks=self.period_in_weeks)
        correct_bon_ids_df = get_correct_bon_id(df=df_sales_for_last_5_weeks,
                                                column="bon_id")

        new_joined_correctDF_row_count = joining_df(df1=df_sales_for_last_5_weeks,
                                                    df2=correct_bon_ids_df,
                                                    column="bon_id",
                                                    way_to_join="leftsemi").count()

        print(new_joined_correctDF_row_count)
        self.assertEqual(old_df_row_count, 19)
        self.assertEqual(new_joined_correctDF_row_count, expected_joined_table_row_count)

    def test_rename_column_of_data_when_len_of_old_names_is_not_equal_len_of_new_names__expect_raises(self):
        old_names = self.test_df_filtered_sales_with_names_articles.columns
        new_columns_names = ["article_id", "quantity", "unit_of_measure", "action_flag", "names_of_articles_gm"]
        with self.assertRaises(ValueError) as error:
            rename_column(df=self.test_df_filtered_sales_with_names_articles,
                          new_names=new_columns_names)
        self.assertEqual(f"The length of the {old_names} and {new_columns_names} lists should be the same.",
                         str(error.exception))

    def test_rename_column_of_data_when_len_of_old_names_is_equal_len_of_new_names(self):
        expected_old_columns_names = ["kl_art_id", "menge", "einh_id", "aktion_fg", "kl_art_bez", "wug_bez", "art_bez"]
        actual_old_columns_names = self.test_df_filtered_sales_with_names_articles.columns

        new_columns_names = ["article_id", "quantity", "unit_of_measure", "action_flag", "names_of_articles_gm",
                             "group_names", "names_of_articles_bg"]

        renamed_df = rename_column(df=self.test_df_filtered_sales_with_names_articles,
                                   new_names=new_columns_names
                                   )

        actual_new_column_names = renamed_df.columns
        expected_new_column_names = new_columns_names
        self.assertEqual(actual_old_columns_names, expected_old_columns_names)
        self.assertEqual(actual_new_column_names, expected_new_column_names)

    def test_sorting_descending_order_if_column_to_sort_is_only_one(self):
        column_to_sort = "Total Menge per one art_id ST"
        df_per_unit = get_data_per_unit_of_measure(df=self.test_df_filtered_sales_with_names_articles,
                                                   column_to_filter="einh_id",
                                                   column_to_group_by="kl_art_id",
                                                   unit_of_measure="ST")
        sorted_df_desc_by_total_menge_col = sorting_data_desc(df=df_per_unit,
                                                              column_to_sort=[column_to_sort])

        sorted_df_per_unit_dict = [res.asDict() for res in sorted_df_desc_by_total_menge_col.collect()]

        self.assertTrue({"kl_art_id": 13913, "Total Menge per one art_id ST": 6} in sorted_df_per_unit_dict)
        self.assertTrue({"kl_art_id": 15899, "Total Menge per one art_id ST": 2} in sorted_df_per_unit_dict)
        self.assertTrue({"kl_art_id": 10468, "Total Menge per one art_id ST": 1} in sorted_df_per_unit_dict)

    def test_sorting_ascending_order_if_column_to_sort_is_only_one(self):
        column_to_sort = "Total Menge per one art_id ST"
        df_per_unit = get_data_per_unit_of_measure(df=self.test_df_filtered_sales_with_names_articles,
                                                   column_to_filter="einh_id",
                                                   column_to_group_by="kl_art_id",
                                                   unit_of_measure="ST")

        sorted_df_asc_by_total_menge_col = sorting_data_asc(df=df_per_unit,
                                                            column_to_sort=[column_to_sort])

        sorted_df_per_unit_dict = [res.asDict() for res in sorted_df_asc_by_total_menge_col.collect()]

        self.assertTrue({"kl_art_id": 10468, "Total Menge per one art_id ST": 1} in sorted_df_per_unit_dict)
        self.assertTrue({"kl_art_id": 15899, "Total Menge per one art_id ST": 2} in sorted_df_per_unit_dict)
        self.assertTrue({"kl_art_id": 13913, "Total Menge per one art_id ST": 6} in sorted_df_per_unit_dict)

    def test_drop_column(self):
        expected_column_names_after_drop = ["kl_art_id", "menge", "aktion_fg", "kl_art_bez", "wug_bez", "art_bez"]
        actual_column_names_after_drop = (drop_columns(self.test_df_filtered_sales_with_names_articles, ["einh_id"]))\
            .columns

        self.assertEqual(actual_column_names_after_drop, expected_column_names_after_drop)


if __name__ == '__main__':
    unittest.main()
