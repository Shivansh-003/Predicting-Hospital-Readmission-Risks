import sys
from pyspark.sql import SparkSession

def main():
    spark = SparkSession.builder \
        .appName("HospitalAI_Verification") \
        .master("spark://spark-master:7077") \
        .config("spark.driver.host", "spark-master") \
        .config("spark.driver.bindAddress", "0.0.0.0") \
        .config("spark.executor.memory", "512m") \
        .config("spark.executor.cores", "1") \
        .getOrCreate()

    numbers = [1, 2, 3, 4, 5]
    rdd = spark.sparkContext.parallelize(numbers)
    result = rdd.reduce(lambda a, b: a + b)

    print(f"==========================================")
    print(f"SPARK VERIFICATION RESULT: sum({numbers}) = {result}")
    print(f"==========================================")

    if result != 15:
        print(f"ERROR: Expected 15 but got {result}", file=sys.stderr)
        spark.stop()
        sys.exit(1)

    spark.stop()
    print("Spark verification completed successfully.")

if __name__ == "__main__":
    main()
