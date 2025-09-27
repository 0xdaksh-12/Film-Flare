import csv
import re

input_file = "../datasets/movies.csv"
output_file = "../datasets/movie_year.csv"

pattern = re.compile(r"\((\d{4})\)")

with open(input_file, "r", encoding="utf-8") as infile, open(
    output_file, "w", newline="", encoding="utf-8"
) as outfile:
    reader = csv.DictReader(infile)
    writer = csv.writer(outfile)
    writer.writerow(["movieId", "year"])

    for row in reader:
        title = row["title"]
        match = pattern.search(title)
        if match:
            year = match.group(1)
            writer.writerow([row["movieId"], year])

        else:
            print(f"No year found in title: {title}")
