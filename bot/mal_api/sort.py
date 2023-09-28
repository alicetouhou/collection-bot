import pandas

# assign dataset
csvData = pandas.read_csv("bot/data/series.csv",
                          header=0, delimiter="|", encoding="utf8")
csvData.sort_values(["name", "type"],
                    axis=0,
                    ascending=[True, True],
                    inplace=True)

csvData.to_csv("bot/data/series.csv", sep="|", index=False)
