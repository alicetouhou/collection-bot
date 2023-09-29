import pandas


pandas.options.mode.chained_assignment = None

# assign dataset
series = pandas.read_csv("bot/data/series.csv",
                         header=0, delimiter="|", encoding="utf8")
buckets = pandas.read_csv("bot/data/bucket_correspondences.csv",
                          header=0, delimiter="|", encoding="utf8")

for index, val in enumerate(buckets["series_id"]):
    series.loc[series['id'] == val, "bucket"] = buckets["bucket_id"][index]

print(series)

series.to_csv("bot/data/series.csv", sep="|", index=False)
