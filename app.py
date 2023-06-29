from flask import Flask, render_template, request, send_file
from flask_sqlalchemy import SQLAlchemy
from fpdf import FPDF

app = Flask(__name__,template_folder='pages')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///dtbase.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

#Our SQLite Database Model
class SSubD(db.Model):
    sno = db.Column(db.Integer, primary_key = True)
    regno = db.Column(db.BigInteger, nullable = False)
    name = db.Column(db.String(100), nullable = False)
    semester = db.Column(db.Integer, nullable = False)
    coursename = db.Column(db.String(100), nullable = False)
    grade = db.Column(db.String(10), nullable = False)

    def __repr__(self) -> str:
        return f"StudentSubjectDetails(regno={self.regno}, name={self.name}, semester={self.semester}, coursename={self.coursename}, grade={self.grade})"

with app.app_context():
    db.create_all()

#Data fetching function
def createData(data):
    r = []
    n = []
    s = []
    c = []
    g = []
    rc = ""
    nc = ""
    sc = ""
    cc = ""
    gc = ""
    eqt = 0
    i = 0
    c.append('COURSE')
    g.append('GRADE')
    print(len(data))
    while(True):

        while(i < len(data) and data[i]!="="):
            i += 1
        if(i == len(data)):
            break
        i += 1
        eqt += 1
        while(i < len(data) and data[i]!=','):
            if eqt % 5 == 1:
                rc = rc + data[i]
            elif eqt % 5 == 2:
                nc = nc + data[i]
            elif eqt % 5 == 3:
                sc = sc + data[i]
            elif eqt % 5 == 4:
                cc = cc + data[i]
            else:
                if((data[i]>='A' and data[i]<='Z') or (data[i]=='+')):
                    gc = gc + data[i]
            i += 1
        if eqt % 5 == 1:
            r.append(rc)
            rc = ""
        elif eqt % 5 == 2:
            n.append(nc)
            nc = ""
        elif eqt % 5 == 3:
            s.append(sc)
            sc = ""
        elif eqt % 5 == 4:
            c.append(cc)
            cc = ""
        else:
            g.append(gc)
            gc = ""
    newdata = [[c[i],g[i]] for i in range(0,len(c))]
    return newdata, n[0], r[0], s[0]

#App renderer and query filterer
@app.route('/',methods=['GET','POST'])
def make_app():
    global gresult
    results = None
    if request.method == 'POST':
        checkno = request.form['rnoin']
        sem = request.form['semin']
        sem = int(sem)
        checkno = int(checkno)
        qry = SSubD.query.filter_by(regno=checkno, semester=sem)
        results = qry.all()
    gresult = results
    return render_template('index.html',results=results)

#PDF Generator
@app.route('/generate',methods=['GET','POST'])
def generate_pdf():
    if request.method == 'POST':
        results = request.form['results']
        data, name, regno, sem = createData(results)
        class PDF(FPDF):
            def create_table(self, table_data, title='', data_size = 10, title_size=12, align_data='L', align_header='L', cell_width='even', x_start='x_default',emphasize_data=[], emphasize_style=None,emphasize_color=(0,0,0)): 
                """
                table_data: 
                            list of lists with first element being list of headers
                title: 
                            (Optional) title of table (optional)
                data_size: 
                            the font size of table data
                title_size: 
                            the font size fo the title of the table
                align_data: 
                            align table data
                            L = left align
                            C = center align
                            R = right align
                align_header: 
                            align table data
                            L = left align
                            C = center align
                            R = right align
                cell_width: 
                            even: evenly distribute cell/column width
                            uneven: base cell size on lenght of cell/column items
                            int: int value for width of each cell/column
                            list of ints: list equal to number of columns with the widht of each cell / column
                x_start: 
                            where the left edge of table should start
                emphasize_data:  
                            which data elements are to be emphasized - pass as list 
                            emphasize_style: the font style you want emphaized data to take
                            emphasize_color: emphasize color (if other than black) 
                
                """
                default_style = self.font_style
                if emphasize_style == None:
                    emphasize_style = default_style
                # default_font = self.font_family
                # default_size = self.font_size_pt
                # default_style = self.font_style
                # default_color = self.color # This does not work
                # Get Width of Columns
                def get_col_widths():
                    col_width = cell_width
                    if col_width == 'even':
                        col_width = self.epw / len(data[0]) - 1  # distribute content evenly   # epw = effective page width (width of page not including margins)
                    elif col_width == 'uneven':
                        col_widths = []
                        # searching through columns for largest sized cell (not rows but cols)
                        for col in range(len(table_data[0])): # for every row
                            longest = 0 
                            for row in range(len(table_data)):
                                cell_value = str(table_data[row][col])
                                value_length = self.get_string_width(cell_value)
                                if value_length > longest:
                                    longest = value_length
                            col_widths.append(longest + 4) # add 4 for padding
                        col_width = col_widths
                                ### compare columns 
                    elif isinstance(cell_width, list):
                        col_width = cell_width  # TODO: convert all items in list to int        
                    else:
                        # TODO: Add try catch
                        col_width = int(col_width)
                    return col_width
                # Convert dict to lol
                # Why? because i built it with lol first and added dict func after
                # Is there performance differences?
                if isinstance(table_data, dict):
                    header = [key for key in table_data]
                    data = []
                    for key in table_data:
                        value = table_data[key]
                        data.append(value)
                    # need to zip so data is in correct format (first, second, third --> not first, first, first)
                    data = [list(a) for a in zip(*data)]
                else:
                    header = table_data[0]
                    data = table_data[1:]
                line_height = self.font_size * 2.5
                col_width = get_col_widths()
                self.set_font(size=title_size)
                # Get starting position of x
                # Determin width of table to get x starting point for centred table
                if x_start == 'C':
                    table_width = 0
                    if isinstance(col_width, list):
                        for width in col_width:
                            table_width += width
                    else: # need to multiply cell width by number of cells to get table width 
                        table_width = col_width * len(table_data[0])
                    # Get x start by subtracting table width from pdf width and divide by 2 (margins)
                    margin_width = self.w - table_width
                    # TODO: Check if table_width is larger than pdf width
                    center_table = margin_width / 2 # only want width of left margin not both
                    x_start = center_table
                    self.set_x(x_start)
                elif isinstance(x_start, int):
                    self.set_x(x_start)
                elif x_start == 'x_default':
                    x_start = self.set_x(self.l_margin)
                # TABLE CREATION #
                # add title
                if title != '':
                    self.multi_cell(0, line_height, title, border=0, align='j', ln=3, max_line_height=self.font_size)
                    self.ln(line_height) # move cursor back to the left margin
                self.set_font(size=data_size)
                # add header
                y1 = self.get_y()
                if x_start:
                    x_left = x_start
                else:
                    x_left = self.get_x()
                x_right = self.epw + x_left
                if  not isinstance(col_width, list):
                    if x_start:
                        self.set_x(x_start)
                    for datum in header:
                        self.multi_cell(col_width, line_height, datum, border=0, align=align_header, ln=3, max_line_height=self.font_size)
                        x_right = self.get_x()
                    self.ln(line_height) # move cursor back to the left margin
                    y2 = self.get_y()
                    self.line(x_left,y1,x_right,y1)
                    self.line(x_left,y2,x_right,y2)
                    for row in data:
                        if x_start:
                            self.set_x(x_start)
                        for datum in row:
                            if datum in emphasize_data:
                                self.set_text_color(*emphasize_color)
                                self.set_font(style=emphasize_style)
                                self.multi_cell(col_width, line_height, datum, border=0, align=align_data, ln=3, max_line_height=self.font_size)
                                self.set_text_color(0,0,0)
                                self.set_font(style=default_style)
                            else:
                                self.multi_cell(col_width, line_height, datum, border=0, align=align_data, ln=3, max_line_height=self.font_size) # ln = 3 - move cursor to right with same vertical offset # this uses an object named self
                        self.ln(line_height) # move cursor back to the left margin
                else:
                    if x_start:
                        self.set_x(x_start)
                    for i in range(len(header)):
                        datum = header[i]
                        self.multi_cell(col_width[i], line_height, datum, border=0, align=align_header, ln=3, max_line_height=self.font_size)
                        x_right = self.get_x()
                    self.ln(line_height) # move cursor back to the left margin
                    y2 = self.get_y()
                    self.line(x_left,y1,x_right,y1)
                    self.line(x_left,y2,x_right,y2)
                    for i in range(len(data)):
                        if x_start:
                            self.set_x(x_start)
                        row = data[i]
                        for i in range(len(row)):
                            datum = row[i]
                            if not isinstance(datum, str):
                                datum = str(datum)
                            adjusted_col_width = col_width[i]
                            if datum in emphasize_data:
                                self.set_text_color(*emphasize_color)
                                self.set_font(style=emphasize_style)
                                self.multi_cell(adjusted_col_width, line_height, datum, border=0, align=align_data, ln=3, max_line_height=self.font_size)
                                self.set_text_color(0,0,0)
                                self.set_font(style=default_style)
                            else:
                                self.multi_cell(adjusted_col_width, line_height, datum, border=0, align=align_data, ln=3, max_line_height=self.font_size) # ln = 3 - move cursor to right with same vertical offset # this uses an object named self
                        self.ln(line_height) # move cursor back to the left margin
                y3 = self.get_y()
                self.line(x_left,y3,x_right,y3)
        pdf = PDF()
        pdf.add_page()
        pdf.set_font("Times", 'B',20)
        pdf.cell(0,20,'Semester Marksheet',border=True,ln=True,align='C')
        pdf.ln(20)
        pdf.set_font("Times", '',13)
        pdf.cell(0,10,"Registration Number: " + regno,ln=True)
        pdf.cell(0,10,"Name: " + name,ln=True)
        pdf.cell(0,10,"Semester: " + sem,ln=True)
        pdf.create_table(table_data=data,title='RESULTS',cell_width=22,x_start='C')
        pdf.cell(0,20,"   ",ln=True)
        pdf.cell(0,10,"OFFICE-SEAL-HERE",ln=True,align='C')
        pdf.output('results.pdf')
    return send_file('results.pdf', download_name='results.pdf')

if __name__=="__main__":
    app.run(debug=True)