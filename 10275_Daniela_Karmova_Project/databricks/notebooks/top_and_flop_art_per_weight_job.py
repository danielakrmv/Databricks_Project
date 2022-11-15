# COMMAND ----------
from pyspark.dbutils import DBUtils

from datetime import date

from uapc_aiacad.common.config import create_config
from uapc_aiacad.common.custom_logging import CustomLogging
from uapc_aiacad.jobs.transformation_jobs.finding_top_and_flop_art_per_weight_job import FindTopAndFlopTenArticlesPerWeightEtlJob
# COMMAND ----------
spark.conf.set("spark.sql.adaptive.enabled", True)  # improves the query performance by re-optimizing the query plan during runtime with the statistics it collects after each stage completion.
spark.conf.set("spark.sql.adaptive.coalescePartitions.enabled", True)
spark.conf.set("spark.sql.inMemoryColumnarStorage.compressed", True) # Spark retrieves only required columns which result in fewer data retrieval and less memory usage
spark.conf.set("spark.sql.adaptive.skewJoin.enabled", True)
# Sometimes we may come across data in partitions that are not evenly distributed, this is called Data Skew.
# Operations such as join perform very slow on this partitions.
# optimizes it by splitting the bigger partitions into smaller
spark.conf.set("spark.databricks.io.cache.enabled", True)
#Disabling the cache does not result in dropping the data that is already in the local storage.
# Instead, it prevents queries from adding new data to the cache and reading data from the cache.
# COMMAND ----------
dbutils = DBUtils()

config_file_path = dbutils.widgets.get("config_file")
config = create_config(config_file_path)
custom_logging = CustomLogging(config['databricks']['logging'])
custom_logging.setup_logging_basic()

try:
    finding_top_and_flop_art_per_weight = FindTopAndFlopTenArticlesPerWeightEtlJob(config=config)
    finding_top_and_flop_art_per_weight.run()
except Exception as e:
    custom_logging.log_uncaught_exception(e)
    raise ValueError("Job run failed!")
finally:
    custom_logging.get_logs(config['databricks']['logging']['filename'] + f'logs_{date.today()}.log', dbutils)
    custom_logging.close_stream()