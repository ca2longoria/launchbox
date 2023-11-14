---
# launchbox

It's a lunchbox!  But also a launcher of boxes.  EC2 instances in this case.

---

### Version actively in development

Full history listed in wiki.

#### v0.1_1.2_2.4

Working toward minor version 2
- [x] get network connecting to newly started instance
  - [~] ENC or something, Elastic Network Connection I think?
    - this wasn't it; it was a Subnet auto-assign public ipv4 setting
  - [x] auto-create one on new instance if specified in profile config file
    - new Subnet with autoassign works for public internet connection
- [ ] buildup steps on start
  - [ ] packages specified in config file
  - [ ] packages actually install

