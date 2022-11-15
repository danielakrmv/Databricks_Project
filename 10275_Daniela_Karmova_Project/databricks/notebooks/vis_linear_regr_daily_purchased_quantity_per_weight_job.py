# COMMAND ----------
from pyspark.dbutils import DBUtils

from datetime import date

from uapc_aiacad.common.config import create_config
from uapc_aiacad.common.custom_logging import CustomLogging
from uapc_aiacad.jobs.visualization_jobs.vis_linear_regr_of_daily_purchased_quantity_per_weight_job import VisDailyDistributedQuantityPerWeightPredictJob
# COMMAND ----------
spark.conf.set("spark.sql.adaptive.enabled", True)
spark.conf.set("spark.sql.adaptive.coalescePartitions.enabled", True)
spark.conf.set("spark.sql.inMemoryColumnarStorage.compressed", True)
spark.conf.set("spark.sql.adaptive.skewJoin.enabled", True)
spark.conf.set("spark.databricks.io.cache.enabled", True)
# COMMAND ----------
dbutils = DBUtils()

config_file_path = dbutils.widgets.get("config_file")
config = create_config(config_file_path)
custom_logging = CustomLogging(config['databricks']['logging'])
custom_logging.setup_logging_basic()

try:
    plot_vis_daily_distributed_quantity_per_weight_linear_regr_job = VisDailyDistributedQuantityPerWeightPredictJob(config=config)
    plot_vis_daily_distributed_quantity_per_weight_linear_regr_job.run()
except Exception as e:
    custom_logging.log_uncaught_exception(e)
    raise ValueError("Job run failed!")
finally:
    custom_logging.get_logs(config['databricks']['logging']['filename'] + f'logs_{date.today()}.log', dbutils)
    custom_logging.close_stream()
