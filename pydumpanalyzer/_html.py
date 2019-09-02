''' this is the home for various html helpers '''

from utility import getUniqueId
from csmlog_setup import getLogger

logger = getLogger(__file__)

def getHtmlLinkString(url, text):
    ''' given a url/text returns an a '''
    return r'<a href="%s">%s</a>' % (url, text)

SEARCH_CODE = '''
<script src="https://ajax.googleapis.com/ajax/libs/jquery/3.4.1/jquery.min.js"></script>
<script>
// This is code for search
$(document).ready(function(){{
  $("#input_{id}").on("keyup", function() {{
    var value = $(this).val().toLowerCase();
    $("#table_{id} tr").filter(function() {{
      $(this).toggle($(this).text().toLowerCase().indexOf(value) > -1)
    }});
  }});
}});
</script>

<input id="input_{id}" type="text" placeholder="Search..." class="{classes}">
'''

TABLE_CONTENT = '''
<table style="width:100%;" class="{classes}">
    <thead style="text-align: left">
        {headers}
    </thead>
    <tbody id="table_{id}">
        {rows}
    </tbody>
</table
'''

FULL_CONTENT = '''
<h2 class="{classes}">{name}</h2>
<div class="{classes}" style="border: 1px solid black;">
{searchCode}
{tableContent}
</div>
'''

class HtmlTable(object):
    ''' this object is used to create an HTML table, with optional search functionality '''
    def __init__(self, tableHeaders, name=None, addSearch=True, classes=None):
        ''' initializer for html table object '''
        self.tableHeaders = tableHeaders
        self.name = name if name is not None else ''
        self.addSearch = addSearch
        self.classes = classes if classes is not None else ''
        self.id = getUniqueId()
        self.rows = []

    @classmethod
    def fromCursor(cls, cursor, name=None, addSearch=True, classes=None):
        ''' helper to get an HtmlTable from a database cursor '''
        if not cursor:
            logger.error("Cursor appears to be invalid")
            return False

        results = cursor.fetchall()
        if not results:
            logger.error("Empty results from valid cursor")
            return False

        keys = results[0]._fields
        retTable = HtmlTable(tableHeaders=keys, name=name, addSearch=addSearch, classes=classes)
        for result in results:
            retTable.addRow(list(result))

        return retTable

    def addRow(self, row):
        ''' adds a row to the table. This row must have the same number of items as the
        original tableHeaders had. '''
        if len(row) != len(self.tableHeaders):
            raise ValueError("number of items in a row (%d) must match number of items in tableHeaders (%d)" % (len(row), len(self.tableHeaders)))

        self.rows.append(row)

    def __html__(self):
        ''' general purpose to-html method for this table '''
        searchCode = ''
        if self.addSearch:
            searchCode += SEARCH_CODE.format(id=self.id, classes=self.classes)

        headerText = '<tr>\n'
        for row in self.tableHeaders:
            headerText += '<th>%s</th>\n' % (row)
        headerText += '</tr>\n'

        rowText = ''
        for row in self.rows:
            rowText += '<tr>\n'
            for colIdx, value in enumerate(row):
                rowText += '<td>%s</td>\n' % (value)
            rowText += '</tr>\n'

        tableContent = TABLE_CONTENT.format(id=self.id, rows=rowText, headers=headerText, classes=self.classes)

        retStr = FULL_CONTENT.format(classes=self.classes, searchCode=searchCode, tableContent=tableContent, name=self.name)
        return retStr


