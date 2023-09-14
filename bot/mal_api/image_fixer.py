import csv
import asyncio
import aiohttp
import imagesize
import io

async def get_image_size(url, session) -> tuple | None:
    try:
        async with session.get(url=url) as response:
            resp = await response.read()
            image = io.BytesIO(resp)
            image_size = imagesize.get(image)
            return image_size
    except Exception as e:
        print("Unable to get url {} due to {}.".format(url, e.__class__))


async def get_image_sizes(urls, offset, splice_length, name) -> list[str]:
    length = 0

    erratas = []
    async with aiohttp.ClientSession() as session:
        iter = 0 + offset
        urls = urls[offset:offset+splice_length]
        print(len(urls))

        for array in urls:
            length += len(array[0])

        for array in urls:
            for url in array[0]:
                size = await get_image_size(url, session)
                iter += 1
                if size[0]/size[1] < 0.62 or size[0]/size[1] > 0.67:
                    #print(f"Errata found: Aspect ratio - {size[0]/size[1]} {iter}/{length} ({url})")
                    erratas.append([url, array[1]])
            if iter % 200 == 0:
                print(f"{name}: {iter - offset}/{length}")
    print(f"Thread {name} Complete!")
    return(erratas)

def get_urls(f):
    reader = csv.reader(f, delimiter="|")
    next(reader)
    urls = []
    data = []
    index = 0
    for x in reader:
        urls.append([x[4].split(","), index])
        data.append([x[0], x[1], x[2], x[3], x[4], x[5], x[6], x[7]])
        index += 1
    return urls, data

async def remove_wrong_erratas(f, filedata):
    erratas = await asyncio.gather(
            get_image_sizes(urls, 0, 1999, "A"),
            get_image_sizes(urls, 2000, 1999, "B"),
            get_image_sizes(urls, 4000, 1999, "C"),
            get_image_sizes(urls, 5000, 1999, "D"),
            get_image_sizes(urls, 6000, 1999, "E"),
            get_image_sizes(urls, 8000, 1999, "F"),
            get_image_sizes(urls, 10000, 1499, "G"),
            get_image_sizes(urls, 11500, 1999, "H"),
            get_image_sizes(urls, 13500, 1999, "I"),
            get_image_sizes(urls, 15500, 2499, "J"),
            get_image_sizes(urls, 18000, 1508, "K"),

        )
    
    combined_erratas = []
    for errata in erratas:
        combined_erratas += errata
    print(len(combined_erratas))
    writer = csv.writer(f, delimiter="|")

    data = filedata

    for errata in combined_erratas:
        images = data[errata[1]][4].split(",")
        if errata[0] in images:
            images.remove(errata[0])
        images = ",".join(images)
        data[errata[1]][4] = images

    for row in data:
        if row[4] == "":
            data.remove(row)

    writer.writerow(("id", "first_name", "last_name", "anime_list", "pictures", "value", "manga_list", "games_list"))
    writer.writerows(data)

file = open("bot/data/db.csv", "r", encoding="utf8")
urls, data = get_urls(file)

write_file = open("bot/data/db.csv", "w", newline='', encoding="utf8")
asyncio.run(remove_wrong_erratas(write_file, data))