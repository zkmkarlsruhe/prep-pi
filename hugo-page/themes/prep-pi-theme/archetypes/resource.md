+++
date = {{ .Date }}
draft = false
weight = 1

title = "{{ replace .Name "-" " " | title }}"
image = "/images/placeholder.png"
file = "/downloads/placeholder.pdf"
+++

{{< content-block "regular" >}}
Detailed content about the resource goes here.
{{< /content-block >}}

{{< content-block "simple" >}}
Simple language content goes here.
{{< /content-block >}}