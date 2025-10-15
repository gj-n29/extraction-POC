from google import genai
from spire.pdf.common import *
from spire.pdf import *
from google import genai
import sys
import os


# use commndline argument for pdf file name
report_name = sys.argv[1]

## Google GenAI API key
client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

# extraction variables
extract_prompt = {}
page_content = {}

## converted content initialised with report filename
document_as_markdown = report_name + "\n\n"

## Prompts....
model = "gemini-2.0-flash"  ## model="gemini-2.5-flash",
convert_prompt = "Faithfully convert this image of a page from a report into markdown format. Include all information, all tables, images, paragraphs, headings, footers and all other items. Do not calculate or derive any data, just report what is in the document without any changes. Do not judge the content or the company performance."

extract_prompt_header = "You are a professional financial analyst reading a financial forecast report. Actual results are typically presented in tabular form under year headings indicating the year number or year and suffix 'A'.  Estimates of the future performance are suffixed 'E'.  Curremcy and multipliers are usually only shown once and apply to the whole document, and this is not always included near the data to which it pertains.  Ensure you show currency, scaling, and units when providing answers.  Scaling can be included in the currency areviation usually with suffixes that include 'm' for millions eg millions of US Dollasrs are USDm, and millions of Indian Rupees are INRm"
extract_prompt_footer = "Be concise and do not make up answers, and do not derive answers. It is acceptable to say data is not available if the item cannot be found in the report.  Indicate which section and page your answer was obtained from. I'll give you $1000 if you are entirely correct."
extract_prompt[0] = (
    "Use use the report data to identify the company name and stock market tickr.  Also list the both current and target share price."
)
extract_prompt[1] = (
    "List the actual sales revenue for each historic year reported, plus revenue for all years for which there are estimates."
)
extract_prompt[2] = (
    "List the actual Earnings Per Share (EPS) for each historic year reported, plus EPS for all years for which there are estimates."
)
extract_prompt[3] = (
    "List the actual Earnings Before Interest and Taxes (EBIT) for each historic year reported, plus EBIT for all years for which there are estimates."
)
extract_prompt[4] = (
    "List the actual Earnings Before Interest, Taxes, Depreciation, and Amortisation (EBITDA) for each historic year reported, plus EBITDA for all years for which there are estimates."
)
extract_prompt[5] = (
    "List the actual Earnings Before Interest, Taxes, Depreciation, Amortisation, and Restructuring or Rent (EBITDAR) for each historic year reported, plus EBITDAR for all years for which there are estimates."
)
extract_prompt[6] = (
    "List the actual Earnings Before Interest and Taxes Margin (EBIT Margin) for each historic year reported, plus EBIT Margin for all years for which there are estimates."
)
extract_prompt[7] = (
    "List the actual Current Assets for each historic year reported, plus Current Assets for all years for which there are estimates."
)
extract_prompt[8] = (
    "List the actual Current Liabilities for each historic year reported, plus Current Liabilities for all years for which there are estimates."
)
extract_prompt[9] = (
    "List the actual Total Liabilities for each historic year reported, plus Total Liabilities for all years for which there are estimates."
)
extract_prompt[10] = (
    "Does the report indicate this stock is a recommendation to buy, sell or hold?  If so, what is the target price and the rationale for the recommendation?"
)


# Create a new PdfDocument object
doc = PdfDocument()
# Load a PDF document
doc.LoadFromFile(report_name)

# Loop through the pages in the document
# for i in range(doc.Pages.Count):
for i in range(10):
    # Save each page as a PNG image
    print(f"Creating image of page {i+1}")
    fileName = "img-{0:d}.png".format(i)
    with doc.SaveAsImage(i) as imageS:
        imageS.Save(fileName)

# Close the PdfDocument object
doc.Close()


# Loop through the pages in the document
for i in range(10):
    # Convert from each PNG image
    print(f"Converting to markdown, page {i+1}")
    # fileName = "img-{0:d}.png".format(i)
    imgName = client.files.upload(file="img-{0:d}.png".format(i))
    page_content[i] = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=[convert_prompt, imgName],
    )
    document_as_markdown += page_content[i].text + "\n"

## create evidence of source document
with open("extracted.md", "w") as f:
    f.write(document_as_markdown)


## new results file
with open("results.md", "w") as f:
    f.write("# Extracted Results from " + report_name + "\n\n")

# Now extract specific information from the markdown document
for i in range(len(extract_prompt)):
    print(f"Extracting data point {i+1}")
    as_reported = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=[
            f"{extract_prompt_header} {extract_prompt[i]} {extract_prompt_footer}",
            document_as_markdown,
        ],
    )
    ## update evidence / results
    with open("results.md", "a") as f:
        f.write("\n*** PROMPT:")
        f.write(extract_prompt[i] + "\n")
        f.write(as_reported.text + "\n")

print("All done - results in results.md")


## Reformat extracted data
ExtractedData = client.files.upload(file="results.md")

## create json output file
with open("results.json", "w") as f:
    f.write("// Extracted Results from " + report_name + "\n\n")

## Company name, stock price, tickr, amnd recommendation in JSON format for easy import to a spreadsheet
format_prompt = "Extract the company name, stock tickr, current stock price, and analysts recommendation represented in JSON format. Values should absolute, without scaling such as thousands or millions. Do not calculate or derive any data, just report what is in the document without any changes. Do not judge the content or the company performance."
print(f"\nFormatting stock info")
print(f"\n=====================")
json_data = client.models.generate_content(
    model="gemini-2.0-flash",
    contents=[f"{format_prompt}", ExtractedData],
)
print(f"{json_data}")
## add to json output file
with open("results.json", "a") as f:
    f.write(f"{json_data}\n")

## Revenue extraction in JSON format for easy import to a spreadsheet
format_prompt = "Extract the sales revenue per year, the currency, and numeric values as columns in a table, represented in JSON format. Values should absolute, without scaling such as thousands or millions. Add a column to the table stating estimate or actual as appropriate for each row. Do not calculate or derive any data, just report what is in the document without any changes. Do not judge the content or the company performance."
print(f"\nFormatting revenue")
print(f"\n==================")
json_data = client.models.generate_content(
    model="gemini-2.0-flash",
    contents=[f"{format_prompt}", ExtractedData],
)
print(f"{json_data}")
## add to json output file
with open("results.json", "a") as f:
    f.write(f"{json_data}\n")

## EPS extraction in JSON format for easy import to a spreadsheet
format_prompt = "Extract the Earnings Per Share (EPS) per year, the currency, and numeric values as columns in a table, represented in JSON format. Values should absolute, without scaling such as thousands or millions. Add a column to the table stating estimate or actual as appropriate for each row. Do not calculate or derive any data, just report what is in the document without any changes."
print(f"\nFormatting EPS")
print(f"\n==============")
json_data = client.models.generate_content(
    model="gemini-2.0-flash",
    contents=[f"{format_prompt}", ExtractedData],
)
print(f"{json_data}")
## add to json output file
with open("results.json", "a") as f:
    f.write(f"{json_data}\n")

print("All formatted - results in results.json")
