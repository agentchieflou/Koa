# Products

**URL:** `SitePages/Products.aspx`. **For:** everyone. **Design:** the canvas artboard *Products*.

Every product Data Czars supports in the PAE, its state today, how to start, what changed, and where to report a
problem. A product is the kernel, or one capability of the team's package a person calls by name (a Spark session,
a profiler, a table compare), or another tool the team supports. The catalog, the status and the releases are lists
filled from the data-czars scan; the page itself only changes when its purpose does.

## Build it with Copilot

From any page, open **Copilot** and ask it to create a page, then paste (`site/out/pages/products.md` has it filled in):

```text
Create a page called "Products" for the Data Czars site. Use only the sections and web parts below, in this order, and use my words exactly. Propose the layout first and wait for my go-ahead.

Title area: Image layout, topic header "Supported in the PAE", title "Products", and the description "Everything Data Czars supports in the PAE, its state today, how to start, and where to report a problem."

1. One-column section, no background. Heading "Product catalog", then a List web part.
2. Two-thirds left section, no background. Left: heading "Releases" and a List web part. Right: heading "Status", a List web part, and a Button web part "Report an issue" linking to Get-help.aspx.
3. One-column section, Neutral background. A Text web part: "New to the kernel? Get started has the access, the setup and your first session. Not sure which product you are using? Ask the Czars in Copilot, or describe what you were doing on Get help and we will route it."
```

## Sections

| # | Section | Web part | Source and settings |
| --- | --- | --- | --- |
| title | Image layout | title area | background `assets/title-products.png`, topic header on |
| 1 | One column, none | List | `Products`, view `Catalog`; command bar on, so people can search |
| 2 | Two-thirds left, none | List | `Releases`, view `All Items` |
| 2 | right column | List, Button | `Products`, view `Status`, size Small; Button to Get-help.aspx |
| 3 | One column, Neutral | Text | |

## Words

All of it is in the prompt. Each product's card says what the scan found in data-czars: its summary, support level,
how to start, docs and repository, and a *Report an issue* link that opens the intake form.

## Finish by hand

1. Title area: upload `assets/title-products.png`, focal point on the right, topic header on.
2. List web parts: list and view as the table says.
3. Products: set each row's **Owner**; the scans leave people empty.
4. Publish, and set the page description: "Every Data Czars product, its state, and how to start."

## Check

- Every card's *Report an issue* opens the intake form.
- The mega menu's Products links land on their sections (`#product-catalog`, `#releases`, `#status`).
