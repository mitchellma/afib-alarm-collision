import requests as r

class fileStation:
    def __init__(self):
        return

    def getList(self, folderpath, sid):
        try:
            #limit to 1000 files for sanity

            fileParam = {"api":"SYNO.FileStation.List", "version":"2", "method":"list", "folder_path":str(folderpath), "limit":1000, "sort_by": "name", "sort_direction": "desc", "_sid":str(sid)}

            response = r.get('http://128.218.209.79:5000/webapi/entry.cgi', params=fileParam)

            response.raise_for_status()

            return response.json()

        except (ValueError, r.exceptions.HTTPError) as err:
            print(err)
            print(response)
            print (folderpath + " was invalid.")

    def downloadFile(self, filepath, sid):
        try:

            fileParam = {"api":"SYNO.FileStation.Download", "version":"2", "method":"download", "path":str(filepath), "mode":"download", "_sid":str(sid)}

            headers = {"Accept-Encoding":"identity"}

            response = r.get('http://128.218.209.79:5000/webapi/entry.cgi', params=fileParam, headers = headers, stream = True)

            response.raise_for_status()

            return response

        except (ValueError, r.exceptions.HTTPError) as err:
            print(err)
            print(response)
            print (filepath + " was invalid.")
            return None
