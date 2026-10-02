from analysis.analyze import analyze

report = analyze("sample_report.pdf")
text = report.model_dump_json(indent=2)
print(text)

with open("sample_output.json", "w") as f:
    f.write(text)
