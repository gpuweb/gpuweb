#include <tree_sitter/parser.h>
#include <wctype.h>
#include <algorithm>
#include <bitset>
#include <cassert>
#include <cstring>
#include <string>
#include <type_traits>
#include <vector>

#define ENABLE_LOGGING 0

#if ENABLE_LOGGING
#define LOG(msg, ...) printf(msg "\n", ##__VA_ARGS__)
#else
#define LOG(...)
#endif

namespace {

/// The possible external tokens matched by this custom scanner.
/// The order of the entries in this enumerator must match the 'externals' in
/// the grammar.js.
enum Token {
  BLOCK_COMMENT,
  DISAMBIGUATE_TEMPLATE,  // A zero-length token used to scan ahead
  TEMPLATE_ARGS_START,
  TEMPLATE_ARGS_END,
  LESS_THAN,           // '<'
  LESS_THAN_EQUAL,     // '<='
  SHIFT_LEFT,          // '<<'
  SHIFT_LEFT_ASSIGN,   // '<<='
  GREATER_THAN,        // '>'
  GREATER_THAN_EQUAL,  // '>='
  SHIFT_RIGHT,         // '>>'
  SHIFT_RIGHT_ASSIGN,  // '>>='

  // A sentinel value used to signal an error has occurred already.
  // https://tree-sitter.github.io/tree-sitter/creating-parsers#other-external-scanner-details
  ERROR,
};

const char* str(Token tok,bool brief=false) {
  switch (tok) {
    case Token::BLOCK_COMMENT:
      return "BLOCK_COMMENT";
    case Token::DISAMBIGUATE_TEMPLATE:
      return "DISAMBIGUATE_TEMPLATE";
    case Token::TEMPLATE_ARGS_START:
      return "TEMPLATE_ARGS_START";
    case Token::TEMPLATE_ARGS_END:
      return "TEMPLATE_ARGS_END";
    case Token::LESS_THAN:
      return brief ? "<" : "LESS_THAN";
    case Token::LESS_THAN_EQUAL:
      return brief ? "<=" : "LESS_THAN_EQUAL";
    case Token::SHIFT_LEFT:
      return brief ? "<<" : "SHIFT_LEFT";
    case Token::SHIFT_LEFT_ASSIGN:
      return brief ? "<<=" : "SHIFT_LEFT_ASSIGN";
    case Token::GREATER_THAN:
      return brief ? ">" : "GREATER_THAN";
    case Token::GREATER_THAN_EQUAL:
      return brief ? ">=" : "GREATER_THAN_EQUAL";
    case Token::SHIFT_RIGHT:
      return brief ? ">>" : "SHIFT_RIGHT";
    case Token::SHIFT_RIGHT_ASSIGN:
      return brief ? ">>=" : "SHIFT_RIGHT_ASSIGN";
    case Token::ERROR:
      return "ERROR";
    default:
      return "<invalid>";
  }
}

using CodePoint = uint32_t;

static constexpr CodePoint kEOF = 0;

struct CodePointRange {
  CodePoint first;  // First code point in the interval
  CodePoint last;   // Last code point in the interval (inclusive)
};

inline bool operator<(CodePoint code_point, CodePointRange range) {
  return code_point < range.first;
}
inline bool operator<(CodePointRange range, CodePoint code_point) {
  return range.last < code_point;
}

// Interval ranges of all code points in the Unicode 14 XID_Start set
// This array needs to be in ascending order.
constexpr CodePointRange kXIDStartRanges[] = {
    {0x00041, 0x0005a}, {0x00061, 0x0007a}, {0x000aa, 0x000aa},
    {0x000b5, 0x000b5}, {0x000ba, 0x000ba}, {0x000c0, 0x000d6},
    {0x000d8, 0x000f6}, {0x000f8, 0x002c1}, {0x002c6, 0x002d1},
    {0x002e0, 0x002e4}, {0x002ec, 0x002ec}, {0x002ee, 0x002ee},
    {0x00370, 0x00374}, {0x00376, 0x00377}, {0x0037b, 0x0037d},
    {0x0037f, 0x0037f}, {0x00386, 0x00386}, {0x00388, 0x0038a},
    {0x0038c, 0x0038c}, {0x0038e, 0x003a1}, {0x003a3, 0x003f5},
    {0x003f7, 0x00481}, {0x0048a, 0x0052f}, {0x00531, 0x00556},
    {0x00559, 0x00559}, {0x00560, 0x00588}, {0x005d0, 0x005ea},
    {0x005ef, 0x005f2}, {0x00620, 0x0064a}, {0x0066e, 0x0066f},
    {0x00671, 0x006d3}, {0x006d5, 0x006d5}, {0x006e5, 0x006e6},
    {0x006ee, 0x006ef}, {0x006fa, 0x006fc}, {0x006ff, 0x006ff},
    {0x00710, 0x00710}, {0x00712, 0x0072f}, {0x0074d, 0x007a5},
    {0x007b1, 0x007b1}, {0x007ca, 0x007ea}, {0x007f4, 0x007f5},
    {0x007fa, 0x007fa}, {0x00800, 0x00815}, {0x0081a, 0x0081a},
    {0x00824, 0x00824}, {0x00828, 0x00828}, {0x00840, 0x00858},
    {0x00860, 0x0086a}, {0x00870, 0x00887}, {0x00889, 0x0088e},
    {0x008a0, 0x008c9}, {0x00904, 0x00939}, {0x0093d, 0x0093d},
    {0x00950, 0x00950}, {0x00958, 0x00961}, {0x00971, 0x00980},
    {0x00985, 0x0098c}, {0x0098f, 0x00990}, {0x00993, 0x009a8},
    {0x009aa, 0x009b0}, {0x009b2, 0x009b2}, {0x009b6, 0x009b9},
    {0x009bd, 0x009bd}, {0x009ce, 0x009ce}, {0x009dc, 0x009dd},
    {0x009df, 0x009e1}, {0x009f0, 0x009f1}, {0x009fc, 0x009fc},
    {0x00a05, 0x00a0a}, {0x00a0f, 0x00a10}, {0x00a13, 0x00a28},
    {0x00a2a, 0x00a30}, {0x00a32, 0x00a33}, {0x00a35, 0x00a36},
    {0x00a38, 0x00a39}, {0x00a59, 0x00a5c}, {0x00a5e, 0x00a5e},
    {0x00a72, 0x00a74}, {0x00a85, 0x00a8d}, {0x00a8f, 0x00a91},
    {0x00a93, 0x00aa8}, {0x00aaa, 0x00ab0}, {0x00ab2, 0x00ab3},
    {0x00ab5, 0x00ab9}, {0x00abd, 0x00abd}, {0x00ad0, 0x00ad0},
    {0x00ae0, 0x00ae1}, {0x00af9, 0x00af9}, {0x00b05, 0x00b0c},
    {0x00b0f, 0x00b10}, {0x00b13, 0x00b28}, {0x00b2a, 0x00b30},
    {0x00b32, 0x00b33}, {0x00b35, 0x00b39}, {0x00b3d, 0x00b3d},
    {0x00b5c, 0x00b5d}, {0x00b5f, 0x00b61}, {0x00b71, 0x00b71},
    {0x00b83, 0x00b83}, {0x00b85, 0x00b8a}, {0x00b8e, 0x00b90},
    {0x00b92, 0x00b95}, {0x00b99, 0x00b9a}, {0x00b9c, 0x00b9c},
    {0x00b9e, 0x00b9f}, {0x00ba3, 0x00ba4}, {0x00ba8, 0x00baa},
    {0x00bae, 0x00bb9}, {0x00bd0, 0x00bd0}, {0x00c05, 0x00c0c},
    {0x00c0e, 0x00c10}, {0x00c12, 0x00c28}, {0x00c2a, 0x00c39},
    {0x00c3d, 0x00c3d}, {0x00c58, 0x00c5a}, {0x00c5d, 0x00c5d},
    {0x00c60, 0x00c61}, {0x00c80, 0x00c80}, {0x00c85, 0x00c8c},
    {0x00c8e, 0x00c90}, {0x00c92, 0x00ca8}, {0x00caa, 0x00cb3},
    {0x00cb5, 0x00cb9}, {0x00cbd, 0x00cbd}, {0x00cdd, 0x00cde},
    {0x00ce0, 0x00ce1}, {0x00cf1, 0x00cf2}, {0x00d04, 0x00d0c},
    {0x00d0e, 0x00d10}, {0x00d12, 0x00d3a}, {0x00d3d, 0x00d3d},
    {0x00d4e, 0x00d4e}, {0x00d54, 0x00d56}, {0x00d5f, 0x00d61},
    {0x00d7a, 0x00d7f}, {0x00d85, 0x00d96}, {0x00d9a, 0x00db1},
    {0x00db3, 0x00dbb}, {0x00dbd, 0x00dbd}, {0x00dc0, 0x00dc6},
    {0x00e01, 0x00e30}, {0x00e32, 0x00e32}, {0x00e40, 0x00e46},
    {0x00e81, 0x00e82}, {0x00e84, 0x00e84}, {0x00e86, 0x00e8a},
    {0x00e8c, 0x00ea3}, {0x00ea5, 0x00ea5}, {0x00ea7, 0x00eb0},
    {0x00eb2, 0x00eb2}, {0x00ebd, 0x00ebd}, {0x00ec0, 0x00ec4},
    {0x00ec6, 0x00ec6}, {0x00edc, 0x00edf}, {0x00f00, 0x00f00},
    {0x00f40, 0x00f47}, {0x00f49, 0x00f6c}, {0x00f88, 0x00f8c},
    {0x01000, 0x0102a}, {0x0103f, 0x0103f}, {0x01050, 0x01055},
    {0x0105a, 0x0105d}, {0x01061, 0x01061}, {0x01065, 0x01066},
    {0x0106e, 0x01070}, {0x01075, 0x01081}, {0x0108e, 0x0108e},
    {0x010a0, 0x010c5}, {0x010c7, 0x010c7}, {0x010cd, 0x010cd},
    {0x010d0, 0x010fa}, {0x010fc, 0x01248}, {0x0124a, 0x0124d},
    {0x01250, 0x01256}, {0x01258, 0x01258}, {0x0125a, 0x0125d},
    {0x01260, 0x01288}, {0x0128a, 0x0128d}, {0x01290, 0x012b0},
    {0x012b2, 0x012b5}, {0x012b8, 0x012be}, {0x012c0, 0x012c0},
    {0x012c2, 0x012c5}, {0x012c8, 0x012d6}, {0x012d8, 0x01310},
    {0x01312, 0x01315}, {0x01318, 0x0135a}, {0x01380, 0x0138f},
    {0x013a0, 0x013f5}, {0x013f8, 0x013fd}, {0x01401, 0x0166c},
    {0x0166f, 0x0167f}, {0x01681, 0x0169a}, {0x016a0, 0x016ea},
    {0x016ee, 0x016f8}, {0x01700, 0x01711}, {0x0171f, 0x01731},
    {0x01740, 0x01751}, {0x01760, 0x0176c}, {0x0176e, 0x01770},
    {0x01780, 0x017b3}, {0x017d7, 0x017d7}, {0x017dc, 0x017dc},
    {0x01820, 0x01878}, {0x01880, 0x018a8}, {0x018aa, 0x018aa},
    {0x018b0, 0x018f5}, {0x01900, 0x0191e}, {0x01950, 0x0196d},
    {0x01970, 0x01974}, {0x01980, 0x019ab}, {0x019b0, 0x019c9},
    {0x01a00, 0x01a16}, {0x01a20, 0x01a54}, {0x01aa7, 0x01aa7},
    {0x01b05, 0x01b33}, {0x01b45, 0x01b4c}, {0x01b83, 0x01ba0},
    {0x01bae, 0x01baf}, {0x01bba, 0x01be5}, {0x01c00, 0x01c23},
    {0x01c4d, 0x01c4f}, {0x01c5a, 0x01c7d}, {0x01c80, 0x01c88},
    {0x01c90, 0x01cba}, {0x01cbd, 0x01cbf}, {0x01ce9, 0x01cec},
    {0x01cee, 0x01cf3}, {0x01cf5, 0x01cf6}, {0x01cfa, 0x01cfa},
    {0x01d00, 0x01dbf}, {0x01e00, 0x01f15}, {0x01f18, 0x01f1d},
    {0x01f20, 0x01f45}, {0x01f48, 0x01f4d}, {0x01f50, 0x01f57},
    {0x01f59, 0x01f59}, {0x01f5b, 0x01f5b}, {0x01f5d, 0x01f5d},
    {0x01f5f, 0x01f7d}, {0x01f80, 0x01fb4}, {0x01fb6, 0x01fbc},
    {0x01fbe, 0x01fbe}, {0x01fc2, 0x01fc4}, {0x01fc6, 0x01fcc},
    {0x01fd0, 0x01fd3}, {0x01fd6, 0x01fdb}, {0x01fe0, 0x01fec},
    {0x01ff2, 0x01ff4}, {0x01ff6, 0x01ffc}, {0x02071, 0x02071},
    {0x0207f, 0x0207f}, {0x02090, 0x0209c}, {0x02102, 0x02102},
    {0x02107, 0x02107}, {0x0210a, 0x02113}, {0x02115, 0x02115},
    {0x02118, 0x0211d}, {0x02124, 0x02124}, {0x02126, 0x02126},
    {0x02128, 0x02128}, {0x0212a, 0x02139}, {0x0213c, 0x0213f},
    {0x02145, 0x02149}, {0x0214e, 0x0214e}, {0x02160, 0x02188},
    {0x02c00, 0x02ce4}, {0x02ceb, 0x02cee}, {0x02cf2, 0x02cf3},
    {0x02d00, 0x02d25}, {0x02d27, 0x02d27}, {0x02d2d, 0x02d2d},
    {0x02d30, 0x02d67}, {0x02d6f, 0x02d6f}, {0x02d80, 0x02d96},
    {0x02da0, 0x02da6}, {0x02da8, 0x02dae}, {0x02db0, 0x02db6},
    {0x02db8, 0x02dbe}, {0x02dc0, 0x02dc6}, {0x02dc8, 0x02dce},
    {0x02dd0, 0x02dd6}, {0x02dd8, 0x02dde}, {0x03005, 0x03007},
    {0x03021, 0x03029}, {0x03031, 0x03035}, {0x03038, 0x0303c},
    {0x03041, 0x03096}, {0x0309d, 0x0309f}, {0x030a1, 0x030fa},
    {0x030fc, 0x030ff}, {0x03105, 0x0312f}, {0x03131, 0x0318e},
    {0x031a0, 0x031bf}, {0x031f0, 0x031ff}, {0x03400, 0x04dbf},
    {0x04e00, 0x0a48c}, {0x0a4d0, 0x0a4fd}, {0x0a500, 0x0a60c},
    {0x0a610, 0x0a61f}, {0x0a62a, 0x0a62b}, {0x0a640, 0x0a66e},
    {0x0a67f, 0x0a69d}, {0x0a6a0, 0x0a6ef}, {0x0a717, 0x0a71f},
    {0x0a722, 0x0a788}, {0x0a78b, 0x0a7ca}, {0x0a7d0, 0x0a7d1},
    {0x0a7d3, 0x0a7d3}, {0x0a7d5, 0x0a7d9}, {0x0a7f2, 0x0a801},
    {0x0a803, 0x0a805}, {0x0a807, 0x0a80a}, {0x0a80c, 0x0a822},
    {0x0a840, 0x0a873}, {0x0a882, 0x0a8b3}, {0x0a8f2, 0x0a8f7},
    {0x0a8fb, 0x0a8fb}, {0x0a8fd, 0x0a8fe}, {0x0a90a, 0x0a925},
    {0x0a930, 0x0a946}, {0x0a960, 0x0a97c}, {0x0a984, 0x0a9b2},
    {0x0a9cf, 0x0a9cf}, {0x0a9e0, 0x0a9e4}, {0x0a9e6, 0x0a9ef},
    {0x0a9fa, 0x0a9fe}, {0x0aa00, 0x0aa28}, {0x0aa40, 0x0aa42},
    {0x0aa44, 0x0aa4b}, {0x0aa60, 0x0aa76}, {0x0aa7a, 0x0aa7a},
    {0x0aa7e, 0x0aaaf}, {0x0aab1, 0x0aab1}, {0x0aab5, 0x0aab6},
    {0x0aab9, 0x0aabd}, {0x0aac0, 0x0aac0}, {0x0aac2, 0x0aac2},
    {0x0aadb, 0x0aadd}, {0x0aae0, 0x0aaea}, {0x0aaf2, 0x0aaf4},
    {0x0ab01, 0x0ab06}, {0x0ab09, 0x0ab0e}, {0x0ab11, 0x0ab16},
    {0x0ab20, 0x0ab26}, {0x0ab28, 0x0ab2e}, {0x0ab30, 0x0ab5a},
    {0x0ab5c, 0x0ab69}, {0x0ab70, 0x0abe2}, {0x0ac00, 0x0d7a3},
    {0x0d7b0, 0x0d7c6}, {0x0d7cb, 0x0d7fb}, {0x0f900, 0x0fa6d},
    {0x0fa70, 0x0fad9}, {0x0fb00, 0x0fb06}, {0x0fb13, 0x0fb17},
    {0x0fb1d, 0x0fb1d}, {0x0fb1f, 0x0fb28}, {0x0fb2a, 0x0fb36},
    {0x0fb38, 0x0fb3c}, {0x0fb3e, 0x0fb3e}, {0x0fb40, 0x0fb41},
    {0x0fb43, 0x0fb44}, {0x0fb46, 0x0fbb1}, {0x0fbd3, 0x0fc5d},
    {0x0fc64, 0x0fd3d}, {0x0fd50, 0x0fd8f}, {0x0fd92, 0x0fdc7},
    {0x0fdf0, 0x0fdf9}, {0x0fe71, 0x0fe71}, {0x0fe73, 0x0fe73},
    {0x0fe77, 0x0fe77}, {0x0fe79, 0x0fe79}, {0x0fe7b, 0x0fe7b},
    {0x0fe7d, 0x0fe7d}, {0x0fe7f, 0x0fefc}, {0x0ff21, 0x0ff3a},
    {0x0ff41, 0x0ff5a}, {0x0ff66, 0x0ff9d}, {0x0ffa0, 0x0ffbe},
    {0x0ffc2, 0x0ffc7}, {0x0ffca, 0x0ffcf}, {0x0ffd2, 0x0ffd7},
    {0x0ffda, 0x0ffdc}, {0x10000, 0x1000b}, {0x1000d, 0x10026},
    {0x10028, 0x1003a}, {0x1003c, 0x1003d}, {0x1003f, 0x1004d},
    {0x10050, 0x1005d}, {0x10080, 0x100fa}, {0x10140, 0x10174},
    {0x10280, 0x1029c}, {0x102a0, 0x102d0}, {0x10300, 0x1031f},
    {0x1032d, 0x1034a}, {0x10350, 0x10375}, {0x10380, 0x1039d},
    {0x103a0, 0x103c3}, {0x103c8, 0x103cf}, {0x103d1, 0x103d5},
    {0x10400, 0x1049d}, {0x104b0, 0x104d3}, {0x104d8, 0x104fb},
    {0x10500, 0x10527}, {0x10530, 0x10563}, {0x10570, 0x1057a},
    {0x1057c, 0x1058a}, {0x1058c, 0x10592}, {0x10594, 0x10595},
    {0x10597, 0x105a1}, {0x105a3, 0x105b1}, {0x105b3, 0x105b9},
    {0x105bb, 0x105bc}, {0x10600, 0x10736}, {0x10740, 0x10755},
    {0x10760, 0x10767}, {0x10780, 0x10785}, {0x10787, 0x107b0},
    {0x107b2, 0x107ba}, {0x10800, 0x10805}, {0x10808, 0x10808},
    {0x1080a, 0x10835}, {0x10837, 0x10838}, {0x1083c, 0x1083c},
    {0x1083f, 0x10855}, {0x10860, 0x10876}, {0x10880, 0x1089e},
    {0x108e0, 0x108f2}, {0x108f4, 0x108f5}, {0x10900, 0x10915},
    {0x10920, 0x10939}, {0x10980, 0x109b7}, {0x109be, 0x109bf},
    {0x10a00, 0x10a00}, {0x10a10, 0x10a13}, {0x10a15, 0x10a17},
    {0x10a19, 0x10a35}, {0x10a60, 0x10a7c}, {0x10a80, 0x10a9c},
    {0x10ac0, 0x10ac7}, {0x10ac9, 0x10ae4}, {0x10b00, 0x10b35},
    {0x10b40, 0x10b55}, {0x10b60, 0x10b72}, {0x10b80, 0x10b91},
    {0x10c00, 0x10c48}, {0x10c80, 0x10cb2}, {0x10cc0, 0x10cf2},
    {0x10d00, 0x10d23}, {0x10e80, 0x10ea9}, {0x10eb0, 0x10eb1},
    {0x10f00, 0x10f1c}, {0x10f27, 0x10f27}, {0x10f30, 0x10f45},
    {0x10f70, 0x10f81}, {0x10fb0, 0x10fc4}, {0x10fe0, 0x10ff6},
    {0x11003, 0x11037}, {0x11071, 0x11072}, {0x11075, 0x11075},
    {0x11083, 0x110af}, {0x110d0, 0x110e8}, {0x11103, 0x11126},
    {0x11144, 0x11144}, {0x11147, 0x11147}, {0x11150, 0x11172},
    {0x11176, 0x11176}, {0x11183, 0x111b2}, {0x111c1, 0x111c4},
    {0x111da, 0x111da}, {0x111dc, 0x111dc}, {0x11200, 0x11211},
    {0x11213, 0x1122b}, {0x11280, 0x11286}, {0x11288, 0x11288},
    {0x1128a, 0x1128d}, {0x1128f, 0x1129d}, {0x1129f, 0x112a8},
    {0x112b0, 0x112de}, {0x11305, 0x1130c}, {0x1130f, 0x11310},
    {0x11313, 0x11328}, {0x1132a, 0x11330}, {0x11332, 0x11333},
    {0x11335, 0x11339}, {0x1133d, 0x1133d}, {0x11350, 0x11350},
    {0x1135d, 0x11361}, {0x11400, 0x11434}, {0x11447, 0x1144a},
    {0x1145f, 0x11461}, {0x11480, 0x114af}, {0x114c4, 0x114c5},
    {0x114c7, 0x114c7}, {0x11580, 0x115ae}, {0x115d8, 0x115db},
    {0x11600, 0x1162f}, {0x11644, 0x11644}, {0x11680, 0x116aa},
    {0x116b8, 0x116b8}, {0x11700, 0x1171a}, {0x11740, 0x11746},
    {0x11800, 0x1182b}, {0x118a0, 0x118df}, {0x118ff, 0x11906},
    {0x11909, 0x11909}, {0x1190c, 0x11913}, {0x11915, 0x11916},
    {0x11918, 0x1192f}, {0x1193f, 0x1193f}, {0x11941, 0x11941},
    {0x119a0, 0x119a7}, {0x119aa, 0x119d0}, {0x119e1, 0x119e1},
    {0x119e3, 0x119e3}, {0x11a00, 0x11a00}, {0x11a0b, 0x11a32},
    {0x11a3a, 0x11a3a}, {0x11a50, 0x11a50}, {0x11a5c, 0x11a89},
    {0x11a9d, 0x11a9d}, {0x11ab0, 0x11af8}, {0x11c00, 0x11c08},
    {0x11c0a, 0x11c2e}, {0x11c40, 0x11c40}, {0x11c72, 0x11c8f},
    {0x11d00, 0x11d06}, {0x11d08, 0x11d09}, {0x11d0b, 0x11d30},
    {0x11d46, 0x11d46}, {0x11d60, 0x11d65}, {0x11d67, 0x11d68},
    {0x11d6a, 0x11d89}, {0x11d98, 0x11d98}, {0x11ee0, 0x11ef2},
    {0x11fb0, 0x11fb0}, {0x12000, 0x12399}, {0x12400, 0x1246e},
    {0x12480, 0x12543}, {0x12f90, 0x12ff0}, {0x13000, 0x1342e},
    {0x14400, 0x14646}, {0x16800, 0x16a38}, {0x16a40, 0x16a5e},
    {0x16a70, 0x16abe}, {0x16ad0, 0x16aed}, {0x16b00, 0x16b2f},
    {0x16b40, 0x16b43}, {0x16b63, 0x16b77}, {0x16b7d, 0x16b8f},
    {0x16e40, 0x16e7f}, {0x16f00, 0x16f4a}, {0x16f50, 0x16f50},
    {0x16f93, 0x16f9f}, {0x16fe0, 0x16fe1}, {0x16fe3, 0x16fe3},
    {0x17000, 0x187f7}, {0x18800, 0x18cd5}, {0x18d00, 0x18d08},
    {0x1aff0, 0x1aff3}, {0x1aff5, 0x1affb}, {0x1affd, 0x1affe},
    {0x1b000, 0x1b122}, {0x1b150, 0x1b152}, {0x1b164, 0x1b167},
    {0x1b170, 0x1b2fb}, {0x1bc00, 0x1bc6a}, {0x1bc70, 0x1bc7c},
    {0x1bc80, 0x1bc88}, {0x1bc90, 0x1bc99}, {0x1d400, 0x1d454},
    {0x1d456, 0x1d49c}, {0x1d49e, 0x1d49f}, {0x1d4a2, 0x1d4a2},
    {0x1d4a5, 0x1d4a6}, {0x1d4a9, 0x1d4ac}, {0x1d4ae, 0x1d4b9},
    {0x1d4bb, 0x1d4bb}, {0x1d4bd, 0x1d4c3}, {0x1d4c5, 0x1d505},
    {0x1d507, 0x1d50a}, {0x1d50d, 0x1d514}, {0x1d516, 0x1d51c},
    {0x1d51e, 0x1d539}, {0x1d53b, 0x1d53e}, {0x1d540, 0x1d544},
    {0x1d546, 0x1d546}, {0x1d54a, 0x1d550}, {0x1d552, 0x1d6a5},
    {0x1d6a8, 0x1d6c0}, {0x1d6c2, 0x1d6da}, {0x1d6dc, 0x1d6fa},
    {0x1d6fc, 0x1d714}, {0x1d716, 0x1d734}, {0x1d736, 0x1d74e},
    {0x1d750, 0x1d76e}, {0x1d770, 0x1d788}, {0x1d78a, 0x1d7a8},
    {0x1d7aa, 0x1d7c2}, {0x1d7c4, 0x1d7cb}, {0x1df00, 0x1df1e},
    {0x1e100, 0x1e12c}, {0x1e137, 0x1e13d}, {0x1e14e, 0x1e14e},
    {0x1e290, 0x1e2ad}, {0x1e2c0, 0x1e2eb}, {0x1e7e0, 0x1e7e6},
    {0x1e7e8, 0x1e7eb}, {0x1e7ed, 0x1e7ee}, {0x1e7f0, 0x1e7fe},
    {0x1e800, 0x1e8c4}, {0x1e900, 0x1e943}, {0x1e94b, 0x1e94b},
    {0x1ee00, 0x1ee03}, {0x1ee05, 0x1ee1f}, {0x1ee21, 0x1ee22},
    {0x1ee24, 0x1ee24}, {0x1ee27, 0x1ee27}, {0x1ee29, 0x1ee32},
    {0x1ee34, 0x1ee37}, {0x1ee39, 0x1ee39}, {0x1ee3b, 0x1ee3b},
    {0x1ee42, 0x1ee42}, {0x1ee47, 0x1ee47}, {0x1ee49, 0x1ee49},
    {0x1ee4b, 0x1ee4b}, {0x1ee4d, 0x1ee4f}, {0x1ee51, 0x1ee52},
    {0x1ee54, 0x1ee54}, {0x1ee57, 0x1ee57}, {0x1ee59, 0x1ee59},
    {0x1ee5b, 0x1ee5b}, {0x1ee5d, 0x1ee5d}, {0x1ee5f, 0x1ee5f},
    {0x1ee61, 0x1ee62}, {0x1ee64, 0x1ee64}, {0x1ee67, 0x1ee6a},
    {0x1ee6c, 0x1ee72}, {0x1ee74, 0x1ee77}, {0x1ee79, 0x1ee7c},
    {0x1ee7e, 0x1ee7e}, {0x1ee80, 0x1ee89}, {0x1ee8b, 0x1ee9b},
    {0x1eea1, 0x1eea3}, {0x1eea5, 0x1eea9}, {0x1eeab, 0x1eebb},
    {0x20000, 0x2a6df}, {0x2a700, 0x2b738}, {0x2b740, 0x2b81d},
    {0x2b820, 0x2cea1}, {0x2ceb0, 0x2ebe0}, {0x2f800, 0x2fa1d},
    {0x30000, 0x3134a},
};

// Number of ranges in kXIDStartRanges
constexpr size_t kNumXIDStartRanges =
    sizeof(kXIDStartRanges) / sizeof(kXIDStartRanges[0]);

// The additional code point interval ranges for the Unicode 14 XID_Continue
// set. This extends the values in kXIDStartRanges.
// This array needs to be in ascending order.
constexpr CodePointRange kXIDContinueRanges[] = {
    {0x00030, 0x00039}, {0x0005f, 0x0005f}, {0x000b7, 0x000b7},
    {0x00300, 0x0036f}, {0x00387, 0x00387}, {0x00483, 0x00487},
    {0x00591, 0x005bd}, {0x005bf, 0x005bf}, {0x005c1, 0x005c2},
    {0x005c4, 0x005c5}, {0x005c7, 0x005c7}, {0x00610, 0x0061a},
    {0x0064b, 0x00669}, {0x00670, 0x00670}, {0x006d6, 0x006dc},
    {0x006df, 0x006e4}, {0x006e7, 0x006e8}, {0x006ea, 0x006ed},
    {0x006f0, 0x006f9}, {0x00711, 0x00711}, {0x00730, 0x0074a},
    {0x007a6, 0x007b0}, {0x007c0, 0x007c9}, {0x007eb, 0x007f3},
    {0x007fd, 0x007fd}, {0x00816, 0x00819}, {0x0081b, 0x00823},
    {0x00825, 0x00827}, {0x00829, 0x0082d}, {0x00859, 0x0085b},
    {0x00898, 0x0089f}, {0x008ca, 0x008e1}, {0x008e3, 0x00903},
    {0x0093a, 0x0093c}, {0x0093e, 0x0094f}, {0x00951, 0x00957},
    {0x00962, 0x00963}, {0x00966, 0x0096f}, {0x00981, 0x00983},
    {0x009bc, 0x009bc}, {0x009be, 0x009c4}, {0x009c7, 0x009c8},
    {0x009cb, 0x009cd}, {0x009d7, 0x009d7}, {0x009e2, 0x009e3},
    {0x009e6, 0x009ef}, {0x009fe, 0x009fe}, {0x00a01, 0x00a03},
    {0x00a3c, 0x00a3c}, {0x00a3e, 0x00a42}, {0x00a47, 0x00a48},
    {0x00a4b, 0x00a4d}, {0x00a51, 0x00a51}, {0x00a66, 0x00a71},
    {0x00a75, 0x00a75}, {0x00a81, 0x00a83}, {0x00abc, 0x00abc},
    {0x00abe, 0x00ac5}, {0x00ac7, 0x00ac9}, {0x00acb, 0x00acd},
    {0x00ae2, 0x00ae3}, {0x00ae6, 0x00aef}, {0x00afa, 0x00aff},
    {0x00b01, 0x00b03}, {0x00b3c, 0x00b3c}, {0x00b3e, 0x00b44},
    {0x00b47, 0x00b48}, {0x00b4b, 0x00b4d}, {0x00b55, 0x00b57},
    {0x00b62, 0x00b63}, {0x00b66, 0x00b6f}, {0x00b82, 0x00b82},
    {0x00bbe, 0x00bc2}, {0x00bc6, 0x00bc8}, {0x00bca, 0x00bcd},
    {0x00bd7, 0x00bd7}, {0x00be6, 0x00bef}, {0x00c00, 0x00c04},
    {0x00c3c, 0x00c3c}, {0x00c3e, 0x00c44}, {0x00c46, 0x00c48},
    {0x00c4a, 0x00c4d}, {0x00c55, 0x00c56}, {0x00c62, 0x00c63},
    {0x00c66, 0x00c6f}, {0x00c81, 0x00c83}, {0x00cbc, 0x00cbc},
    {0x00cbe, 0x00cc4}, {0x00cc6, 0x00cc8}, {0x00cca, 0x00ccd},
    {0x00cd5, 0x00cd6}, {0x00ce2, 0x00ce3}, {0x00ce6, 0x00cef},
    {0x00d00, 0x00d03}, {0x00d3b, 0x00d3c}, {0x00d3e, 0x00d44},
    {0x00d46, 0x00d48}, {0x00d4a, 0x00d4d}, {0x00d57, 0x00d57},
    {0x00d62, 0x00d63}, {0x00d66, 0x00d6f}, {0x00d81, 0x00d83},
    {0x00dca, 0x00dca}, {0x00dcf, 0x00dd4}, {0x00dd6, 0x00dd6},
    {0x00dd8, 0x00ddf}, {0x00de6, 0x00def}, {0x00df2, 0x00df3},
    {0x00e31, 0x00e31}, {0x00e33, 0x00e3a}, {0x00e47, 0x00e4e},
    {0x00e50, 0x00e59}, {0x00eb1, 0x00eb1}, {0x00eb3, 0x00ebc},
    {0x00ec8, 0x00ecd}, {0x00ed0, 0x00ed9}, {0x00f18, 0x00f19},
    {0x00f20, 0x00f29}, {0x00f35, 0x00f35}, {0x00f37, 0x00f37},
    {0x00f39, 0x00f39}, {0x00f3e, 0x00f3f}, {0x00f71, 0x00f84},
    {0x00f86, 0x00f87}, {0x00f8d, 0x00f97}, {0x00f99, 0x00fbc},
    {0x00fc6, 0x00fc6}, {0x0102b, 0x0103e}, {0x01040, 0x01049},
    {0x01056, 0x01059}, {0x0105e, 0x01060}, {0x01062, 0x01064},
    {0x01067, 0x0106d}, {0x01071, 0x01074}, {0x01082, 0x0108d},
    {0x0108f, 0x0109d}, {0x0135d, 0x0135f}, {0x01369, 0x01371},
    {0x01712, 0x01715}, {0x01732, 0x01734}, {0x01752, 0x01753},
    {0x01772, 0x01773}, {0x017b4, 0x017d3}, {0x017dd, 0x017dd},
    {0x017e0, 0x017e9}, {0x0180b, 0x0180d}, {0x0180f, 0x01819},
    {0x018a9, 0x018a9}, {0x01920, 0x0192b}, {0x01930, 0x0193b},
    {0x01946, 0x0194f}, {0x019d0, 0x019da}, {0x01a17, 0x01a1b},
    {0x01a55, 0x01a5e}, {0x01a60, 0x01a7c}, {0x01a7f, 0x01a89},
    {0x01a90, 0x01a99}, {0x01ab0, 0x01abd}, {0x01abf, 0x01ace},
    {0x01b00, 0x01b04}, {0x01b34, 0x01b44}, {0x01b50, 0x01b59},
    {0x01b6b, 0x01b73}, {0x01b80, 0x01b82}, {0x01ba1, 0x01bad},
    {0x01bb0, 0x01bb9}, {0x01be6, 0x01bf3}, {0x01c24, 0x01c37},
    {0x01c40, 0x01c49}, {0x01c50, 0x01c59}, {0x01cd0, 0x01cd2},
    {0x01cd4, 0x01ce8}, {0x01ced, 0x01ced}, {0x01cf4, 0x01cf4},
    {0x01cf7, 0x01cf9}, {0x01dc0, 0x01dff}, {0x0203f, 0x02040},
    {0x02054, 0x02054}, {0x020d0, 0x020dc}, {0x020e1, 0x020e1},
    {0x020e5, 0x020f0}, {0x02cef, 0x02cf1}, {0x02d7f, 0x02d7f},
    {0x02de0, 0x02dff}, {0x0302a, 0x0302f}, {0x03099, 0x0309a},
    {0x0a620, 0x0a629}, {0x0a66f, 0x0a66f}, {0x0a674, 0x0a67d},
    {0x0a69e, 0x0a69f}, {0x0a6f0, 0x0a6f1}, {0x0a802, 0x0a802},
    {0x0a806, 0x0a806}, {0x0a80b, 0x0a80b}, {0x0a823, 0x0a827},
    {0x0a82c, 0x0a82c}, {0x0a880, 0x0a881}, {0x0a8b4, 0x0a8c5},
    {0x0a8d0, 0x0a8d9}, {0x0a8e0, 0x0a8f1}, {0x0a8ff, 0x0a909},
    {0x0a926, 0x0a92d}, {0x0a947, 0x0a953}, {0x0a980, 0x0a983},
    {0x0a9b3, 0x0a9c0}, {0x0a9d0, 0x0a9d9}, {0x0a9e5, 0x0a9e5},
    {0x0a9f0, 0x0a9f9}, {0x0aa29, 0x0aa36}, {0x0aa43, 0x0aa43},
    {0x0aa4c, 0x0aa4d}, {0x0aa50, 0x0aa59}, {0x0aa7b, 0x0aa7d},
    {0x0aab0, 0x0aab0}, {0x0aab2, 0x0aab4}, {0x0aab7, 0x0aab8},
    {0x0aabe, 0x0aabf}, {0x0aac1, 0x0aac1}, {0x0aaeb, 0x0aaef},
    {0x0aaf5, 0x0aaf6}, {0x0abe3, 0x0abea}, {0x0abec, 0x0abed},
    {0x0abf0, 0x0abf9}, {0x0fb1e, 0x0fb1e}, {0x0fe00, 0x0fe0f},
    {0x0fe20, 0x0fe2f}, {0x0fe33, 0x0fe34}, {0x0fe4d, 0x0fe4f},
    {0x0ff10, 0x0ff19}, {0x0ff3f, 0x0ff3f}, {0x0ff9e, 0x0ff9f},
    {0x101fd, 0x101fd}, {0x102e0, 0x102e0}, {0x10376, 0x1037a},
    {0x104a0, 0x104a9}, {0x10a01, 0x10a03}, {0x10a05, 0x10a06},
    {0x10a0c, 0x10a0f}, {0x10a38, 0x10a3a}, {0x10a3f, 0x10a3f},
    {0x10ae5, 0x10ae6}, {0x10d24, 0x10d27}, {0x10d30, 0x10d39},
    {0x10eab, 0x10eac}, {0x10f46, 0x10f50}, {0x10f82, 0x10f85},
    {0x11000, 0x11002}, {0x11038, 0x11046}, {0x11066, 0x11070},
    {0x11073, 0x11074}, {0x1107f, 0x11082}, {0x110b0, 0x110ba},
    {0x110c2, 0x110c2}, {0x110f0, 0x110f9}, {0x11100, 0x11102},
    {0x11127, 0x11134}, {0x11136, 0x1113f}, {0x11145, 0x11146},
    {0x11173, 0x11173}, {0x11180, 0x11182}, {0x111b3, 0x111c0},
    {0x111c9, 0x111cc}, {0x111ce, 0x111d9}, {0x1122c, 0x11237},
    {0x1123e, 0x1123e}, {0x112df, 0x112ea}, {0x112f0, 0x112f9},
    {0x11300, 0x11303}, {0x1133b, 0x1133c}, {0x1133e, 0x11344},
    {0x11347, 0x11348}, {0x1134b, 0x1134d}, {0x11357, 0x11357},
    {0x11362, 0x11363}, {0x11366, 0x1136c}, {0x11370, 0x11374},
    {0x11435, 0x11446}, {0x11450, 0x11459}, {0x1145e, 0x1145e},
    {0x114b0, 0x114c3}, {0x114d0, 0x114d9}, {0x115af, 0x115b5},
    {0x115b8, 0x115c0}, {0x115dc, 0x115dd}, {0x11630, 0x11640},
    {0x11650, 0x11659}, {0x116ab, 0x116b7}, {0x116c0, 0x116c9},
    {0x1171d, 0x1172b}, {0x11730, 0x11739}, {0x1182c, 0x1183a},
    {0x118e0, 0x118e9}, {0x11930, 0x11935}, {0x11937, 0x11938},
    {0x1193b, 0x1193e}, {0x11940, 0x11940}, {0x11942, 0x11943},
    {0x11950, 0x11959}, {0x119d1, 0x119d7}, {0x119da, 0x119e0},
    {0x119e4, 0x119e4}, {0x11a01, 0x11a0a}, {0x11a33, 0x11a39},
    {0x11a3b, 0x11a3e}, {0x11a47, 0x11a47}, {0x11a51, 0x11a5b},
    {0x11a8a, 0x11a99}, {0x11c2f, 0x11c36}, {0x11c38, 0x11c3f},
    {0x11c50, 0x11c59}, {0x11c92, 0x11ca7}, {0x11ca9, 0x11cb6},
    {0x11d31, 0x11d36}, {0x11d3a, 0x11d3a}, {0x11d3c, 0x11d3d},
    {0x11d3f, 0x11d45}, {0x11d47, 0x11d47}, {0x11d50, 0x11d59},
    {0x11d8a, 0x11d8e}, {0x11d90, 0x11d91}, {0x11d93, 0x11d97},
    {0x11da0, 0x11da9}, {0x11ef3, 0x11ef6}, {0x16a60, 0x16a69},
    {0x16ac0, 0x16ac9}, {0x16af0, 0x16af4}, {0x16b30, 0x16b36},
    {0x16b50, 0x16b59}, {0x16f4f, 0x16f4f}, {0x16f51, 0x16f87},
    {0x16f8f, 0x16f92}, {0x16fe4, 0x16fe4}, {0x16ff0, 0x16ff1},
    {0x1bc9d, 0x1bc9e}, {0x1cf00, 0x1cf2d}, {0x1cf30, 0x1cf46},
    {0x1d165, 0x1d169}, {0x1d16d, 0x1d172}, {0x1d17b, 0x1d182},
    {0x1d185, 0x1d18b}, {0x1d1aa, 0x1d1ad}, {0x1d242, 0x1d244},
    {0x1d7ce, 0x1d7ff}, {0x1da00, 0x1da36}, {0x1da3b, 0x1da6c},
    {0x1da75, 0x1da75}, {0x1da84, 0x1da84}, {0x1da9b, 0x1da9f},
    {0x1daa1, 0x1daaf}, {0x1e000, 0x1e006}, {0x1e008, 0x1e018},
    {0x1e01b, 0x1e021}, {0x1e023, 0x1e024}, {0x1e026, 0x1e02a},
    {0x1e130, 0x1e136}, {0x1e140, 0x1e149}, {0x1e2ae, 0x1e2ae},
    {0x1e2ec, 0x1e2f9}, {0x1e8d0, 0x1e8d6}, {0x1e944, 0x1e94a},
    {0x1e950, 0x1e959}, {0x1fbf0, 0x1fbf9}, {0xe0100, 0xe01ef},
};

// Number of ranges in kXIDContinueRanges
constexpr size_t kNumXIDContinueRanges =
    sizeof(kXIDContinueRanges) / sizeof(kXIDContinueRanges[0]);

/// @param code_point the input code_point
/// @return true if the code_point is part of the XIDStart unicode set
bool is_xid_start(CodePoint code_point) {
  // Fast path for ASCII.
  if ((code_point >= 'a' && code_point <= 'z') ||
      (code_point >= 'A' && code_point <= 'Z')) {
    return true;
  }
  // With [a-zA-Z] handled, nothing less then the next sequence start can be
  // XIDStart, so filter them all out. This catches most of the common symbols
  // that are used in ASCII.
  if (code_point < 0x000aa) {
    return false;
  }
  return std::binary_search(kXIDStartRanges,
                            kXIDStartRanges + kNumXIDStartRanges, code_point);
}

/// @param code_point the input code_point
/// @return true if the code_point is part of the XIDContinue unicode set
bool is_xid_continue(CodePoint code_point) {
  // Short circuit ASCII. The binary search will find these last, but most
  // of our current source is ASCII, so handle them quicker.
  if ((code_point >= '0' && code_point <= '9') || code_point == '_') {
    return true;
  }
  return is_xid_start(code_point) ||
         std::binary_search(kXIDContinueRanges,
                            kXIDContinueRanges + kNumXIDContinueRanges,
                            code_point);
}

/// @return true if @p code_point is considered a whitespace
bool is_space(CodePoint code_point) {
  switch (code_point) {
    case 0x0020:
    case 0x0009:
    case 0x000a:
    case 0x000b:
    case 0x000c:
    case 0x000d:
    case 0x0085:
    case 0x200e:
    case 0x200f:
    case 0x2028:
    case 0x2029:
      return true;
    default:
      return false;
  }
}

/// A fixed capacity, dynamic sized queue of bits (expressed as bools)
template <size_t CAPACITY_IN_BITS>
class BitQueue {
 public:
  /// @param index the index of the bit starting from the front
  /// @return the bit value
  auto operator[](size_t index) {
    assert(index < count());  // TODO(dneto): this should error out.
    return bits_[(index + read_offset_) % CAPACITY_IN_BITS];
  }

  /// Removes the bit at the front of the queue
  /// @returns the value of the bit that was removed
  bool pop_front() {
    assert(count_ > 0);
    bool value = (*this)[0];
    count_--;
    read_offset_++;
    return value;
  }

  /// Appends a bit to the back of the queue
  void push_back(bool value) {
    assert(count_ < CAPACITY_IN_BITS);
    count_++;
    (*this)[count_ - 1] = value;
  }

  /// @returns true if the queue holds no bits.
  bool empty() const { return count_ == 0; }

  /// @returns the number of bits held by the queue.
  size_t count() const { return count_; }

 private:
  std::bitset<CAPACITY_IN_BITS> bits_;
  size_t count_ = 0;        // number of bits contained
  size_t read_offset_ = 0;  // read offset in bits
                            //
#if ENABLE_LOGGING
 public:
  void to_chars(std::string& str) {
    std::stringstream ss;
    ss << count_ << ":";
    for (auto i = 0; i < count_; ++i) {
      bool is_template = (*this)[i];
      ss << (is_template ? "#" : ".");
    }
    str = ss.str();
  }
#endif
};

class Lexer {
 public:
  Lexer(TSLexer* l) : lexer_(l) {}

  /// Advances the lexer by one code point.
  void advance() { lexer_->advance(lexer_, /* whitespace */ false); }

  /// Returns the next code point, advancing the lexer by one code point.
  CodePoint next() {
    // TODO(dneto): should assert !lexer_->eof(lexer_)
    CodePoint lookahead = lexer_->lookahead;
    advance();
    return lookahead;
  }

  /// @return the next code point without advancing the lexer, or kEOF if there
  /// are no more code points
  CodePoint peek() { return lexer_->eof(lexer_) ? kEOF : lexer_->lookahead; }

  /// @return true if the next code point is equal to @p code_point.
  /// @note if the code point was found, then the lexer is advanced to that code
  /// point.
  bool match(CodePoint code_point) {
    if (peek() == code_point) {
      advance();
      return true;
    }
    return false;
  }

  /// @return true if the next code point is found in @p code_points.
  /// @note if the code point was found, then the lexer is advanced to that code
  /// point.
  bool match_anyof(std::initializer_list<CodePoint> code_points) {
    for (CodePoint code_point : code_points) {
      if (match(code_point)) {
        return true;
      }
    }
    return false;
  }

  /// Attempts to match an identifier pattern that starts with XIDStart followed by
  /// any number of XIDContinue code points.
  bool match_identifier() {
    if (!is_xid_start(peek())) {
      return false;
    }

    bool is_ascii = true;
    if (CodePoint start = next(); start < 0x80) {
    } else {
      is_ascii = false;
    }

    while (true) {
      if (!is_xid_continue(peek())) {
        break;
      }
      if (CodePoint code_point = next(); code_point < 0x80) {
      } else {
        is_ascii = false;
      }
    }

    if (is_ascii) {
      LOG("ident is ascii");
    } else {
      LOG("ident");
    }

    return true;
  }

  /// Attempts to match a /* block comment */
  bool match_block_comment() {
    // TODO(dneto): Need to un-advance if matched '/' but not '*'
    if (!match('/') || !match('*')) {
      return false;
    }

    size_t nesting = 1;
    while (nesting > 0 && !match(kEOF)) {
      // TODO(dneto): If we match '/' but not '*' there is no way to un-advance
      // back to make '/' the lookahead.
      if (match('/') && match('*')) {
        nesting++;
      // TODO(dneto): Same here, need to be able to un-advance to before '*'
      } else if (match('*') && match('/')) {
        nesting--;
      } else {
        next();
      }
    }
    return true;
  }

  /// Advances the lexer while the next code point is considered whitespace
  void skip_whitespace() {
    while (is_space(peek())) {
      lexer_->advance(lexer_, /* whitespace */ true);
    }
  }

 private:
  TSLexer* lexer_;
};

struct Scanner {
  struct State {
    BitQueue<64> lt_is_tmpl;  // Queue of disambiguated '<'
    BitQueue<64> gt_is_tmpl;  // Queue of disambiguated '>'
    bool empty() const { return lt_is_tmpl.empty() && gt_is_tmpl.empty(); }
  };
  State state;
  static_assert(sizeof(State) < TREE_SITTER_SERIALIZATION_BUFFER_SIZE);
  // State is trivially copyable, so it can be serialized and deserialized
  // with memcpy.
  static_assert(std::is_trivially_copyable<State>::value);

  /// Updates #state with the disambiguated '<' and '>' tokens.
  /// The following assumptions are made on entry:
  /// * lexer has just advanced to the end of an identifier
  /// On exit, all '<' and '>' template tokens will be paired up to the closing
  /// '>' for the first '<'.
  void classify_template_args(Lexer& lexer) {
    LOG("classify_template_args()");

    if (!lexer.match('<')) {
      LOG("  missing '<'");
      return;
    }

    // The current expression nesting depth.
    size_t expr_depth = 0;

    // A stack of '<' tokens. Each is a candidate for the start of a template list.
    // Used to pair '<' and '>' tokens at the same expression depth.
    struct StackEntry {
      size_t index;       // Index of the opening '>' in lt_is_tmpl
      size_t expr_depth;  // The value of 'expr_depth' for the opening '<'
    };
    // The stack of unclosed candidates for template-list starts.
    std::vector<StackEntry> lt_stack;

    LOG("classify_template_args() '<' (initial)");
    lt_stack.push_back(StackEntry{state.lt_is_tmpl.count(), expr_depth});
    // Default to less-than (or less-than-equal, or left-shift, or left-shift-equal)
    state.lt_is_tmpl.push_back(false);

    while (!lt_stack.empty() && !lexer.match(kEOF)) {
      lexer.skip_whitespace();

      // TODO: skip line-ending comments.
      if (lexer.match_block_comment()) {
        continue;
      }

      // A template list can't contain an assignment or a compound assignment.
      // There is logic below which clears the stack when reaching one of those.
      // It looks for a '=' code point.  But we still want to allow
      // comparison operations inside expressions. So we must pre-emptively
      // allow operators: == >= <= !=

      // Look for a nested template-list.
      if (lexer.match_identifier()) {
        lexer.skip_whitespace(); // TODO: Skip comments
        if (lexer.match('<')) {
          LOG("classify_template_args() '<' after ident");
          // Record this '<' in state.lt_is_tmpl, initially treating this as the operator
          // in an expression (less-than, less-than, equal, left-shift, or left-shift-equal).
          // If this '<' is recorded in lt_stack, and a corresponding '>' is found, then this
          // will be transformed into a template-start token.
          state.lt_is_tmpl.push_back(false);

          if (lexer.match('=')) {
            // We entered the loop at "ident<=". No template arg can start with '=',
            // so consider "<=" to be a single token.
            // Litmus test: "alias z = a<b<=c>;"
          } else if (lexer.match('<')) {
            // We entered the loop at "ident<<". No template arg can start with '<',
            // so consider "<<" to be a single token.
            // Litmus test: "alias z = a<b<<c>;"
            state.lt_is_tmpl.push_back(false);
          } else {
            lt_stack.push_back(StackEntry{state.lt_is_tmpl.count()-1, expr_depth});
          }
        }
        continue;
      }

      // Each '<' must be recorded in the lt_is_tmpl queue.
      // Each '>' must be recorded in the gt_is_tmpl queue.

      if (lexer.match('<')) {
        // Litmus test: "alias z =a<1<<c<d>()>;"
        LOG("classify_template_args() '<'");
        state.lt_is_tmpl.push_back(false);
        continue;
      }

      if (lexer.match('>')) {
        LOG("classify_template_args() '>'");
        if (!lt_stack.empty() && lt_stack.back().expr_depth == expr_depth) {
          LOG("   TEMPLATE MATCH");
          state.gt_is_tmpl.push_back(true);
          state.lt_is_tmpl[lt_stack.back().index] = true;
          lt_stack.pop_back();
        } else {
          LOG("   non-template '>'");
          state.gt_is_tmpl.push_back(false);
          // Pre-emptvely allow >= as a comparison operator:
          // Skip over '=', if present.
          lexer.match('=');
        }
        continue;
      }

      // Pre-emptively allow the != operator.
      // As a side effect, allow unary negation operator !
      if (lexer.match('!')) {
        lexer.match('=');
        continue;
      }

      CodePoint was = lexer.peek();
      if (lexer.match_anyof({'(', '['})) {
        LOG("   %c expr_depth++", static_cast<int>(was));
        // Entering a nested expression
        expr_depth++;
        continue;
      }

      if (lexer.match_anyof({')', ']'})) {
        LOG("   %c expr_depth--", static_cast<int>(was));
        // Exiting a nested expression
        // Pop the stack until we return to the current expression
        // expr_depth
        while (!lt_stack.empty() && lt_stack.back().expr_depth == expr_depth) {
          lt_stack.pop_back();
        }
        if (expr_depth > 0) {
          expr_depth--;
        }
        continue;
      }

      was = lexer.peek();
      if (lexer.match('=')) {
        // A subtle point. The '=' we just matched might be the start of a
        // syntactic token, or the end of a compound-assignment operator like +=
        // In either case, it's fine to proceed with the logic below.

        if (lexer.match('=')) {
          // Pre-emptively allow equality ==
          continue;
        }
        // A template list can't contain an assignment, because an expression
        // can't contain an assignment.
        // This might be a regular assignment, or the tail end of a compound
        // assignment.
        LOG("   %c expression terminator", was);
        expr_depth = 0;
        lt_stack.clear();
        continue;
      }

      was = lexer.peek();
      if (lexer.match_anyof({';', '{', ':'})) {
        LOG("   %c expression terminator", was);
        // Expression terminating tokens. No template list can
        // hold these code points, so clear the stack and expression depth.
        expr_depth = 0;
        lt_stack.clear();
        continue;
      }

      bool short_circuit = false;
      if (lexer.match('&')) {
        short_circuit = lexer.match('&');
      } else if (lexer.match('|')) {
        short_circuit = lexer.match('|');
      }
      if (short_circuit) {
        LOG("   short-circuiting expression");
        // Treat 'a < b || c > d' as a logical binary operator of two
        // comparison operators instead of a single template argument
        // 'b||c'. Use parentheses around 'b||c' to parse as a
        // template argument list.
        while (!lt_stack.empty() && lt_stack.back().expr_depth == expr_depth) {
          lt_stack.pop_back();
        }
        continue;
      }

      LOG("   skip: '%c'",char(lexer.peek()));
      lexer.next();
    }
  }

  std::string valids(const bool* const valid_symbols) {
    std::string result;
    for (int i = 0; i < static_cast<int>(ERROR) ; i++) {
      result += std::string(valid_symbols[i] ? "+" : "_");
    }
    for (int i = 0; i < static_cast<int>(ERROR) ; i++) {
      if (valid_symbols[i]) {
        result += std::string(" ") + str(static_cast<Token>(i),true);
      }
    }
    return result;
  }

  /// The external token scanner function. Handles block comments and
  /// template-argument-list vs less-than / greater-than disambiguation.
  /// @return true if lexer->result_symbol was assigned a Token, or
  /// false if the token should be taken from the regular WGSL tree-sitter
  /// grammar.
  bool scan(TSLexer* ts_lexer, const bool* const valid_symbols) {
    Lexer lexer{ts_lexer};

    LOG("scan: '%c' [%u] %s", char(lexer.peek()), unsigned(ts_lexer->get_column(ts_lexer)), valids(valid_symbols).c_str());

    if (valid_symbols[Token::ERROR]) {
      ts_lexer->result_symbol = Token::ERROR;
      return true;
    }

    if (valid_symbols[Token::DISAMBIGUATE_TEMPLATE]) {
      // The parser is telling us the _disambiguate_template token
      // may appear at the current position.
      // The next token may be the start of a template list, so
      // scan forward and use the token-list disambiguation
      // algorithm to mark template-list-start and template-list-end
      // tokens.  These are recorded in the lt and gt bit queues.

      // Call mark_end so that we can "advance" past codepoints without
      // automatically including them in the resulting token.
      ts_lexer->mark_end(ts_lexer);
      ts_lexer->result_symbol = Token::DISAMBIGUATE_TEMPLATE;

      // TODO(dneto): should also skip comments, both line comments
      // and block comments.
      // https://github.com/gpuweb/gpuweb/issues/3876
      lexer.skip_whitespace();
      if (lexer.peek() == '<') {
        if (state.lt_is_tmpl.empty()) {
          classify_template_args(lexer);
        }
      }

      // This has to return true so that Treesitter will save
      // the state generated by the disambiguation scan.
      return true;
    }

    lexer.skip_whitespace();

    auto match = [&](Token token) {
      ts_lexer->mark_end(ts_lexer);
      ts_lexer->result_symbol = token;
      return true;
    };

    // TODO(dneto): checkpoint and rewind if failed.
    if (lexer.match_block_comment()) {
      return match(Token::BLOCK_COMMENT);
    }

    // TODO(dneto): Check valid array first.
    if (lexer.match('<')) {
      if (!state.lt_is_tmpl.empty() && state.lt_is_tmpl.pop_front()) {
        return match(Token::TEMPLATE_ARGS_START);
      }
      if (lexer.match('=')) {
        return match(Token::LESS_THAN_EQUAL);
      }
      if (lexer.match('<')) {
        // Consume the '<' in the lt queue.
        // Litmus test: "alias z = a<1<<c<d>()>;"
        if (!state.lt_is_tmpl.empty()) {
          state.lt_is_tmpl.pop_front();
        }
        if (lexer.match('=')) {
          return match(Token::SHIFT_LEFT_ASSIGN);
        }
        return match(Token::SHIFT_LEFT);
      }
      return match(Token::LESS_THAN);
    }

    // TODO(dneto): check valid array first.
    if (lexer.match('>')) {
      if (!state.gt_is_tmpl.empty() && state.gt_is_tmpl.pop_front()) {
        return match(Token::TEMPLATE_ARGS_END);
      }
      if (lexer.match('=')) {
        return match(Token::GREATER_THAN_EQUAL);
      }
      if (lexer.match('>')) {
        // Consume the '>' in the gt queue.
        if (!state.gt_is_tmpl.empty()) {
          state.gt_is_tmpl.pop_front();
        }
        if (lexer.match('=')) {
          return match(Token::SHIFT_RIGHT_ASSIGN);
        }
        return match(Token::SHIFT_RIGHT);
      }
      return match(Token::GREATER_THAN);
    }

    return false;  // Use regular parsing
  }

  /// Serializes the scanner state into @p buffer.
  unsigned serialize(char* buffer) {
    if (state.empty()) {
      return 0;
    }
#if ENABLE_LOGGING
      std::string lt_str;  state.lt_is_tmpl.to_chars(lt_str);
      std::string gt_str;  state.gt_is_tmpl.to_chars(gt_str);
      LOG("serialize(lt_is_tmpl: %s, gt_is_tmpl: %s)",
          lt_str.c_str(), gt_str.c_str());
#endif
    size_t bytes_written = 0;
    auto write = [&](const void* data, size_t num_bytes) {
      assert(bytes_written + num_bytes <=
             TREE_SITTER_SERIALIZATION_BUFFER_SIZE);
      memcpy(buffer + bytes_written, data, num_bytes);
      bytes_written += num_bytes;
    };
    write(&state.lt_is_tmpl, sizeof(state.lt_is_tmpl));
    write(&state.gt_is_tmpl, sizeof(state.gt_is_tmpl));
    // TODO(dneto): implicit conversion be narrowing.
    return bytes_written;
  }

  /// Deserializes the scanner state from @p buffer.
  void deserialize(const char* const buffer, unsigned length) {
    if (length == 0) {
      state = {};
    } else {
      size_t bytes_read = 0;
      auto read = [&](void* data, size_t num_bytes) {
        assert(bytes_read + num_bytes <= length);
        memcpy(data, buffer + bytes_read, num_bytes);
        bytes_read += num_bytes;
      };
      read(&state.lt_is_tmpl, sizeof(state.lt_is_tmpl));
      read(&state.gt_is_tmpl, sizeof(state.gt_is_tmpl));
#if ENABLE_LOGGING
      std::string lt_str;  state.lt_is_tmpl.to_chars(lt_str);
      std::string gt_str;  state.gt_is_tmpl.to_chars(gt_str);
      LOG("deserialize(lt_is_tmpl: %s, gt_is_tmpl: %s)",
          lt_str.c_str(), gt_str.c_str());
#endif
      assert(bytes_read == length);
    }
  }
};

}  // anonymous namespace

extern "C" {
// Called once when language is set on a parser.
// Allocates memory for storing scanner state.
void* tree_sitter_wgsl_external_scanner_create() {
  return new Scanner();
}

// Called once parser is deleted or different language set.
// Frees memory storing scanner state.
void tree_sitter_wgsl_external_scanner_destroy(void* const payload) {
  Scanner* const scanner = static_cast<Scanner*>(payload);
  delete scanner;
}

// Called whenever this scanner recognizes a token.
// Serializes scanner state into buffer.
unsigned tree_sitter_wgsl_external_scanner_serialize(void* const payload,
                                                     char* const buffer) {
  Scanner* scanner = static_cast<Scanner*>(payload);
  return scanner->serialize(buffer);
}

// Called when handling edits and ambiguities.
// Deserializes scanner state from buffer.
void tree_sitter_wgsl_external_scanner_deserialize(void* const payload,
                                                   const char* const buffer,
                                                   unsigned const length) {
  Scanner* const scanner = static_cast<Scanner*>(payload);
  scanner->deserialize(buffer, length);
}

// Scans for tokens.
bool tree_sitter_wgsl_external_scanner_scan(void* const payload,
                                            TSLexer* const lexer,
                                            const bool* const valid_symbols) {
  Scanner* const scanner = static_cast<Scanner*>(payload);
  if (scanner->scan(lexer, valid_symbols)) {
    LOG("scan returned: %s", str(static_cast<Token>(lexer->result_symbol)));
    return true;
  }
  return false;
}

}  // extern "C"
