#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""CSV2HTML：総理大臣と徳川幕府の情報「CSV」からWebページ「HTML」を生成。"""
__author__ = 'AOKI Atsushi'
__version__ = '1.0.7'
__date__ = '2021/01/10 (Created: 2016/01/01)'

# import datetime
import os

from primeministers.io import IO
from messaging import  Interval
# pylint: disable=R0201
# R0201: Method could be a function (no-self-use)

class Writer(IO):
	"""ライタ：情報のテーブルをHTMLページとして書き出す。"""

	def __init__(self, output_table):
		"""ライタのコンストラクタ。HTMLページを基にするテーブルを受け取る。"""
		super().__init__(output_table)
		

	def perform(self):
		"""HTMLページを基にするテーブルから、インデックスファイル(index_html)に書き出す。"""

		class_attributes = self.attributes().__class__
		base_directory = class_attributes.base_directory()
		index_html = class_attributes.index_html()

		html_filename = os.path.join(base_directory, index_html)
		with open(html_filename, 'w', encoding='utf-8') as a_file:
			self.write_header(a_file)
			self.write_body(a_file)
			self.write_footer(a_file)

	def write_body(self, file):
		"""ボディを書き出す。つまり、属性リストを書き出し、タプル群を書き出す。"""

		caption = self.attributes().__class__.caption_string()
		file.write('<div class="belt">\n')
		file.write('<h2>' + caption + '</h2>\n')
		file.write('</div>\n')
		file.write('<table class="belt" summary="table">\n')
		file.write('<tbody>\n')
		file.write('<tr>\n')
		file.write('<td>\n')
		file.write('<table class="content" summary="table">\n')
		file.write('<tbody>\n')

		# 1. 属性リスト（見出し行）を書き出す
		names = self.attributes().names()
		file.write('<tr>\n')

		def write_name(index):
			file.write('<td class="center-pink"><strong>' + str(names[index]) + '</strong></td>\n')

		Interval(0, lambda index: index < len(names), lambda index: index + 1).for_each(write_name)
		file.write('</tr>\n')

		# 2. タプル群（データ行）を書き出す
		tuples = self.table().tuples()

		def write_tuple(row_index):
			values = tuples[row_index].values()
			td_class = 'center-blue' if row_index % 2 == 0 else 'center-yellow'
			file.write('<tr>\n')

			def write_value(col_index):
				file.write('<td class="' + td_class + '">' + str(values[col_index]) + '</td>\n')

			Interval(0, lambda col_index: col_index < len(values), lambda col_index: col_index + 1).for_each(write_value)
			file.write('</tr>\n')

		Interval(0, lambda row_index: row_index < len(tuples), lambda row_index: row_index + 1).for_each(write_tuple)

		file.write('</tbody>\n')
		file.write('</table>\n')
		file.write('</td>\n')
		file.write('</tr>\n')
		file.write('</tbody>\n')
		file.write('</table>\n')
		

	def write_footer(self, file):
		"""フッタを書き出す。"""
		file.write("<hr>")
		file.write("<div class='right-small'>Created by AOKI Atsushi (CSV2HTML written by Python) 2017/01/11 17:34:25</div>")
		

	def write_header(self, file):
		"""ヘッダを書き出す。"""
		title = self.attributes().title_string()
		file.write('<meta http-equiv="Content-Style-Type" content="text/css">\n')
		file.write('<meta http-equiv="Content-Type" content="text/html; charset=UTF-8">\n')
		file.write('<meta http-equiv="Content-Script-Type" content="text/javascript">\n')
		file.write('<meta name="keywords" content="'+title+'">\n')
		file.write('<meta name="description" content="'+title+'">\n')
		file.write('<meta name="author" content="AOKI Atsushi">\n')
		file.write('<link rel="index" href="index.html">\n')
		file.write("""<style type="text/css">
<!--
body {
	background-color : #ffffff;
	margin : 20px;
	padding : 10px;
	font-family : serif;
	font-size : 10pt;
}
a {
	text-decoration : underline;
	color : #000000;
}
a:link {
	background-color : #ffddbb;
}
a:visited {
	background-color : #ccffcc;
}
a:hover {
	background-color : #dddddd;
}
a:active {
	background-color : #dddddd;
}
div.belt {
	background-color : #eeeeee;
	padding : 0px 4px;
}
div.right-small {
	text-align : right;
	font-size : 8pt;
}
img.borderless {
	border-width : 0px;
	vertical-align : middle;
}
table.belt {
	border-style : solid;
	border-width : 0px;
	border-color : #000000;
	background-color : #ffffff;
	padding : 0px 0px;
	width : 100%;
}
table.content {
	border-style : solid;
	border-width : 0px;
	border-color : #000000;
	padding : 2px 2px;
}
td.center-blue {
	padding : 2px 2px;
	text-align : center;
	background-color : #ddeeff;
}
td.center-pink {
	padding : 2px 2px;
	text-align : center;
	background-color : #ffddee;
}
td.center-yellow {
	padding : 2px 2px;
	text-align : center;
	background-color : #ffffcc;
}
-->
</style>
""")
		file.write("<title>"+ title +"</title>\n")
		
