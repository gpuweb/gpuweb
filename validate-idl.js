const WebIDL2 = require("webidl2");
const fs = require("fs");

const fileName = process.argv[2];

const textToValidate = fs.readFileSync(fileName, "utf8");

try {
  const tree = WebIDL2.parse(textToValidate);
  const text = WebIDL2.write(tree);
  console.log("IDL seems to be valid.");
} catch (e) {
  console.error(e);
  throw e;
}
