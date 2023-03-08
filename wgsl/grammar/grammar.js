// Copyright (C) [2023] World Wide Web Consortium,
        // (Massachusetts Institute of Technology, European Research Consortium for
        // Informatics and Mathematics, Keio University, Beihang).
        // All Rights Reserved.
        //
        // This work is distributed under the W3C (R) Software License [1] in the hope
        // that it will be useful, but WITHOUT ANY WARRANTY; without even the implied
        // warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
        //
        // [1] http://www.w3.org/Consortium/Legal/copyright-software

        // **** This file is auto-generated. Do not edit. ****

                module.exports = grammar({
            name: 'wgsl',

            externals: $ => [
                $._block_comment,
                $._disambiguate_template,
                $._template_args_start,
                $._template_args_end,
                $._less_than,
                $._less_than_equal,
                $._shift_left,
                $._shift_left_assign,
                $._greater_than,
                $._greater_than_equal,
                $._shift_right,
                $._shift_right_assign,
                $._error_sentinel,
            ],

            extras: $ => [
                $._comment,
                $._block_comment,
                $._blankspace,
            ],

            inline: $ => [
                $.global_decl,
                $._reserved,
            ],

            // WGSL has no parsing conflicts.
            conflicts: $ => [],

            word: $ => $.ident_pattern_token,

            rules: {
       
        translation_unit: $ => seq(optional(repeat1($.global_directive)), optional(repeat1($.global_decl))),
        global_directive: $ => choice(
            $.diagnostic_directive,
            $.enable_directive,
            $.requires_directive
        ),
        global_decl: $ => choice(
            token(';'),
            seq($.global_variable_decl, token(';')),
            seq($.global_value_decl, token(';')),
            seq($.type_alias_decl, token(';')),
            $.struct_decl,
            $.function_decl,
            seq($.const_assert_statement, token(';'))
        ),
        bool_literal: $ => choice(
            token('true'),
            token('false')
        ),
        int_literal: $ => choice(
            $.decimal_int_literal,
            $.hex_int_literal
        ),
        decimal_int_literal: $ => choice(
            token(/0[iu]?/),
            token(/[1-9][0-9]*[iu]?/)
        ),
        hex_int_literal: $ => token(/0[xX][0-9a-fA-F]+[iu]?/),
        float_literal: $ => choice(
            $.decimal_float_literal,
            $.hex_float_literal
        ),
        decimal_float_literal: $ => choice(
            token(/0[fh]/),
            token(/[1-9][0-9]*[fh]/),
            token(/[0-9]*\.[0-9]+([eE][+-]?[0-9]+)?[fh]?/),
            token(/[0-9]+\.[0-9]*([eE][+-]?[0-9]+)?[fh]?/),
            token(/[0-9]+[eE][+-]?[0-9]+[fh]?/)
        ),
        hex_float_literal: $ => choice(
            token(/0[xX][0-9a-fA-F]*\.[0-9a-fA-F]+([pP][+-]?[0-9]+[fh]?)?/),
            token(/0[xX][0-9a-fA-F]+\.[0-9a-fA-F]*([pP][+-]?[0-9]+[fh]?)?/),
            token(/0[xX][0-9a-fA-F]+[pP][+-]?[0-9]+[fh]?/)
        ),
        diagnostic_directive: $ => seq(token('diagnostic'), $.diagnostic_control, token(';')),
        literal: $ => choice(
            $.int_literal,
            $.float_literal,
            $.bool_literal
        ),
        ident: $ => seq($.ident_pattern_token, $._disambiguate_template),
        member_ident: $ => $.ident_pattern_token,
        diagnostic_rule_name: $ => $.ident_pattern_token,
        template_list: $ => seq($._template_args_start, $.template_arg_comma_list, $._template_args_end),
        template_arg_comma_list: $ => seq($.template_arg_expression, optional(repeat1(seq(token(','), $.template_arg_expression))), optional(token(','))),
        template_arg_expression: $ => $.expression,
        attribute: $ => choice(
            seq(token('@'), token('align'), token('('), $.expression, $.attrib_end),
            seq(token('@'), token('binding'), token('('), $.expression, $.attrib_end),
            seq(token('@'), token('builtin'), token('('), $.expression, $.attrib_end),
            seq(token('@'), token('const')),
            seq(token('@'), token('diagnostic'), $.diagnostic_control),
            seq(token('@'), token('group'), token('('), $.expression, $.attrib_end),
            seq(token('@'), token('id'), token('('), $.expression, $.attrib_end),
            seq(token('@'), token('interpolate'), token('('), $.expression, $.attrib_end),
            seq(token('@'), token('interpolate'), token('('), $.expression, token(','), $.expression, $.attrib_end),
            seq(token('@'), token('invariant')),
            seq(token('@'), token('location'), token('('), $.expression, $.attrib_end),
            seq(token('@'), token('must_use')),
            seq(token('@'), token('size'), token('('), $.expression, $.attrib_end),
            seq(token('@'), token('workgroup_size'), token('('), $.expression, $.attrib_end),
            seq(token('@'), token('workgroup_size'), token('('), $.expression, token(','), $.expression, $.attrib_end),
            seq(token('@'), token('workgroup_size'), token('('), $.expression, token(','), $.expression, token(','), $.expression, $.attrib_end),
            seq(token('@'), token('vertex')),
            seq(token('@'), token('fragment')),
            seq(token('@'), token('compute'))
        ),
        attrib_end: $ => seq(optional(token(',')), token(')')),
        diagnostic_control: $ => seq(token('('), $.severity_control_name, token(','), $.diagnostic_rule_name, $.attrib_end),
        struct_decl: $ => seq(token('struct'), $.ident, $.struct_body_decl),
        struct_body_decl: $ => seq(token('{'), $.struct_member, optional(repeat1(seq(token(','), $.struct_member))), optional(token(',')), token('}')),
        struct_member: $ => seq(optional(repeat1($.attribute)), $.member_ident, token(':'), $.type_specifier),
        type_alias_decl: $ => seq(token('alias'), $.ident, token('='), $.type_specifier),
        type_specifier: $ => $.template_elaborated_ident,
        template_elaborated_ident: $ => seq($.ident, $._disambiguate_template, optional($.template_list)),
        variable_or_value_statement: $ => choice(
            $.variable_decl,
            seq($.variable_decl, token('='), $.expression),
            seq(token('let'), $.optionally_typed_ident, token('='), $.expression),
            seq(token('const'), $.optionally_typed_ident, token('='), $.expression)
        ),
        variable_decl: $ => seq(token('var'), $._disambiguate_template, optional($.template_list), $.optionally_typed_ident),
        optionally_typed_ident: $ => seq($.ident, optional(seq(token(':'), $.type_specifier))),
        global_variable_decl: $ => seq(optional(repeat1($.attribute)), $.variable_decl, optional(seq(token('='), $.expression))),
        global_value_decl: $ => choice(
            seq(token('const'), $.optionally_typed_ident, token('='), $.expression),
            seq(optional(repeat1($.attribute)), token('override'), $.optionally_typed_ident, optional(seq(token('='), $.expression)))
        ),
        primary_expression: $ => choice(
            $.template_elaborated_ident,
            $.call_expression,
            $.literal,
            $.paren_expression
        ),
        call_expression: $ => $.call_phrase,
        call_phrase: $ => seq($.template_elaborated_ident, $.argument_expression_list),
        paren_expression: $ => seq(token('('), $.expression, token(')')),
        argument_expression_list: $ => seq(token('('), optional($.expression_comma_list), token(')')),
        expression_comma_list: $ => seq($.expression, optional(repeat1(seq(token(','), $.expression))), optional(token(','))),
        component_or_swizzle_specifier: $ => choice(
            seq(token('['), $.expression, token(']'), optional($.component_or_swizzle_specifier)),
            seq(token('.'), $.member_ident, optional($.component_or_swizzle_specifier)),
            seq(token('.'), $.swizzle_name, optional($.component_or_swizzle_specifier))
        ),
        unary_expression: $ => choice(
            $.singular_expression,
            seq(token('-'), $.unary_expression),
            seq(token('!'), $.unary_expression),
            seq(token('~'), $.unary_expression),
            seq(token('*'), $.unary_expression),
            seq(token('&'), $.unary_expression)
        ),
        singular_expression: $ => seq($.primary_expression, optional($.component_or_swizzle_specifier)),
        lhs_expression: $ => choice(
            seq($.core_lhs_expression, optional($.component_or_swizzle_specifier)),
            seq(token('*'), $.lhs_expression),
            seq(token('&'), $.lhs_expression)
        ),
        core_lhs_expression: $ => choice(
            seq($.ident, $._disambiguate_template),
            seq(token('('), $.lhs_expression, token(')'))
        ),
        multiplicative_expression: $ => choice(
            $.unary_expression,
            seq($.multiplicative_expression, $.multiplicative_operator, $.unary_expression)
        ),
        multiplicative_operator: $ => choice(
            token('*'),
            token('/'),
            token('%')
        ),
        additive_expression: $ => choice(
            $.multiplicative_expression,
            seq($.additive_expression, $.additive_operator, $.multiplicative_expression)
        ),
        additive_operator: $ => choice(
            token('+'),
            token('-')
        ),
        shift_expression: $ => choice(
            $.additive_expression,
            seq($.unary_expression, $._shift_left, $.unary_expression),
            seq($.unary_expression, $._shift_right, $.unary_expression)
        ),
        relational_expression: $ => choice(
            $.shift_expression,
            seq($.shift_expression, $._less_than, $.shift_expression),
            seq($.shift_expression, $._greater_than, $.shift_expression),
            seq($.shift_expression, $._less_than_equal, $.shift_expression),
            seq($.shift_expression, $._greater_than_equal, $.shift_expression),
            seq($.shift_expression, token('=='), $.shift_expression),
            seq($.shift_expression, token('!='), $.shift_expression)
        ),
        short_circuit_and_expression: $ => choice(
            $.relational_expression,
            seq($.short_circuit_and_expression, token('&&'), $.relational_expression)
        ),
        short_circuit_or_expression: $ => choice(
            $.relational_expression,
            seq($.short_circuit_or_expression, token('||'), $.relational_expression)
        ),
        binary_or_expression: $ => choice(
            $.unary_expression,
            seq($.binary_or_expression, token('|'), $.unary_expression)
        ),
        binary_and_expression: $ => choice(
            $.unary_expression,
            seq($.binary_and_expression, token('&'), $.unary_expression)
        ),
        binary_xor_expression: $ => choice(
            $.unary_expression,
            seq($.binary_xor_expression, token('^'), $.unary_expression)
        ),
        bitwise_expression: $ => choice(
            seq($.binary_and_expression, token('&'), $.unary_expression),
            seq($.binary_or_expression, token('|'), $.unary_expression),
            seq($.binary_xor_expression, token('^'), $.unary_expression)
        ),
        expression: $ => choice(
            $.relational_expression,
            seq($.short_circuit_or_expression, token('||'), $.relational_expression),
            seq($.short_circuit_and_expression, token('&&'), $.relational_expression),
            $.bitwise_expression
        ),
        compound_statement: $ => seq(optional(repeat1($.attribute)), token('{'), optional(repeat1($.statement)), token('}')),
        assignment_statement: $ => choice(
            seq($.lhs_expression, choice(token('='), $.compound_assignment_operator), $.expression),
            seq(token('_'), token('='), $.expression)
        ),
        compound_assignment_operator: $ => choice(
            token('+='),
            token('-='),
            token('*='),
            token('/='),
            token('%='),
            token('&='),
            token('|='),
            token('^='),
            $._shift_right_assign,
            $._shift_left_assign
        ),
        increment_statement: $ => seq($.lhs_expression, token('++')),
        decrement_statement: $ => seq($.lhs_expression, token('--')),
        if_statement: $ => seq(optional(repeat1($.attribute)), $.if_clause, optional(repeat1($.else_if_clause)), optional($.else_clause)),
        if_clause: $ => seq(token('if'), $.expression, $.compound_statement),
        else_if_clause: $ => seq(token('else'), token('if'), $.expression, $.compound_statement),
        else_clause: $ => seq(token('else'), $.compound_statement),
        switch_statement: $ => seq(optional(repeat1($.attribute)), token('switch'), $.expression, $.switch_body),
        switch_body: $ => seq(optional(repeat1($.attribute)), token('{'), repeat1($.switch_clause), token('}')),
        switch_clause: $ => choice(
            $.case_clause,
            $.default_alone_clause
        ),
        case_clause: $ => seq(token('case'), $.case_selectors, optional(token(':')), $.compound_statement),
        default_alone_clause: $ => seq(token('default'), optional(token(':')), $.compound_statement),
        case_selectors: $ => seq($.case_selector, optional(repeat1(seq(token(','), $.case_selector))), optional(token(','))),
        case_selector: $ => choice(
            token('default'),
            $.expression
        ),
        loop_statement: $ => seq(optional(repeat1($.attribute)), token('loop'), optional(repeat1($.attribute)), token('{'), optional(repeat1($.statement)), optional($.continuing_statement), token('}')),
        for_statement: $ => seq(optional(repeat1($.attribute)), token('for'), token('('), $.for_header, token(')'), $.compound_statement),
        for_header: $ => seq(optional($.for_init), token(';'), optional($.expression), token(';'), optional($.for_update)),
        for_init: $ => choice(
            $.variable_or_value_statement,
            $.variable_updating_statement,
            $.func_call_statement
        ),
        for_update: $ => choice(
            $.variable_updating_statement,
            $.func_call_statement
        ),
        while_statement: $ => seq(optional(repeat1($.attribute)), token('while'), $.expression, $.compound_statement),
        break_statement: $ => token('break'),
        break_if_statement: $ => seq(token('break'), token('if'), $.expression, token(';')),
        continue_statement: $ => token('continue'),
        continuing_statement: $ => seq(token('continuing'), $.continuing_compound_statement),
        continuing_compound_statement: $ => seq(optional(repeat1($.attribute)), token('{'), optional(repeat1($.statement)), optional($.break_if_statement), token('}')),
        return_statement: $ => seq(token('return'), optional($.expression)),
        func_call_statement: $ => $.call_phrase,
        const_assert_statement: $ => seq(token('const_assert'), $.expression),
        statement: $ => choice(
            token(';'),
            seq($.return_statement, token(';')),
            $.if_statement,
            $.switch_statement,
            $.loop_statement,
            $.for_statement,
            $.while_statement,
            seq($.func_call_statement, token(';')),
            seq($.variable_or_value_statement, token(';')),
            seq($.break_statement, token(';')),
            seq($.continue_statement, token(';')),
            seq(token('discard'), token(';')),
            seq($.variable_updating_statement, token(';')),
            $.compound_statement,
            seq($.const_assert_statement, token(';'))
        ),
        variable_updating_statement: $ => choice(
            $.assignment_statement,
            $.increment_statement,
            $.decrement_statement
        ),
        function_decl: $ => seq(optional(repeat1($.attribute)), $.function_header, $.compound_statement),
        function_header: $ => seq(token('fn'), $.ident, token('('), optional($.param_list), token(')'), optional(seq(token('->'), optional(repeat1($.attribute)), $.template_elaborated_ident))),
        param_list: $ => seq($.param, optional(repeat1(seq(token(','), $.param))), optional(token(','))),
        param: $ => seq(optional(repeat1($.attribute)), $.ident, token(':'), $.type_specifier),
        enable_directive: $ => seq(token('enable'), $.enable_extension_list, token(';')),
        enable_extension_list: $ => seq($.enable_extension_name, optional(repeat1(seq(token(','), $.enable_extension_name))), optional(token(','))),
        requires_directive: $ => seq(token('requires'), $.software_extension_list, token(';')),
        software_extension_list: $ => seq($.software_extension_name, optional(repeat1(seq(token(','), $.software_extension_name))), optional(token(','))),
        enable_extension_name: $ => $.ident_pattern_token,
        software_extension_name: $ => $.ident_pattern_token,
        ident_pattern_token: $ => token(/([_\p{XID_Start}][\p{XID_Continue}]+)|([\p{XID_Start}])/uy),
        severity_control_name: $ => choice(
            token('error'),
            token('warning'),
            token('info'),
            token('off')
        ),
        swizzle_name: $ => choice(
            token('/[rgba]/'),
            token('/[rgba][rgba]/'),
            token('/[rgba][rgba][rgba]/'),
            token('/[rgba][rgba][rgba][rgba]/'),
            token('/[xyzw]/'),
            token('/[xyzw][xyzw]/'),
            token('/[xyzw][xyzw][xyzw]/'),
            token('/[xyzw][xyzw][xyzw][xyzw]/')
        ),
        _reserved: $ => choice(
            token('NULL'),
            token('Self'),
            token('abstract'),
            token('active'),
            token('alignas'),
            token('alignof'),
            token('as'),
            token('asm'),
            token('asm_fragment'),
            token('async'),
            token('attribute'),
            token('auto'),
            token('await'),
            token('become'),
            token('binding_array'),
            token('cast'),
            token('catch'),
            token('class'),
            token('co_await'),
            token('co_return'),
            token('co_yield'),
            token('coherent'),
            token('column_major'),
            token('common'),
            token('compile'),
            token('compile_fragment'),
            token('concept'),
            token('const_cast'),
            token('consteval'),
            token('constexpr'),
            token('constinit'),
            token('crate'),
            token('debugger'),
            token('decltype'),
            token('delete'),
            token('demote'),
            token('demote_to_helper'),
            token('do'),
            token('dynamic_cast'),
            token('enum'),
            token('explicit'),
            token('export'),
            token('extends'),
            token('extern'),
            token('external'),
            token('fallthrough'),
            token('filter'),
            token('final'),
            token('finally'),
            token('friend'),
            token('from'),
            token('fxgroup'),
            token('get'),
            token('goto'),
            token('groupshared'),
            token('highp'),
            token('impl'),
            token('implements'),
            token('import'),
            token('inline'),
            token('instanceof'),
            token('interface'),
            token('layout'),
            token('lowp'),
            token('macro'),
            token('macro_rules'),
            token('match'),
            token('mediump'),
            token('meta'),
            token('mod'),
            token('module'),
            token('move'),
            token('mut'),
            token('mutable'),
            token('namespace'),
            token('new'),
            token('nil'),
            token('noexcept'),
            token('noinline'),
            token('nointerpolation'),
            token('noperspective'),
            token('null'),
            token('nullptr'),
            token('of'),
            token('operator'),
            token('package'),
            token('packoffset'),
            token('partition'),
            token('pass'),
            token('patch'),
            token('pixelfragment'),
            token('precise'),
            token('precision'),
            token('premerge'),
            token('priv'),
            token('protected'),
            token('pub'),
            token('public'),
            token('readonly'),
            token('ref'),
            token('regardless'),
            token('register'),
            token('reinterpret_cast'),
            token('require'),
            token('resource'),
            token('restrict'),
            token('self'),
            token('set'),
            token('shared'),
            token('sizeof'),
            token('smooth'),
            token('snorm'),
            token('static'),
            token('static_assert'),
            token('static_cast'),
            token('std'),
            token('subroutine'),
            token('super'),
            token('target'),
            token('template'),
            token('this'),
            token('thread_local'),
            token('throw'),
            token('trait'),
            token('try'),
            token('type'),
            token('typedef'),
            token('typeid'),
            token('typename'),
            token('typeof'),
            token('union'),
            token('unless'),
            token('unorm'),
            token('unsafe'),
            token('unsized'),
            token('use'),
            token('using'),
            token('varying'),
            token('virtual'),
            token('volatile'),
            token('wgsl'),
            token('where'),
            token('with'),
            token('writeonly'),
            token('yield')
        ),
        ident: $ => seq($.ident_pattern_token, $._disambiguate_template),
        _comment: $ => token(/\/\/.*/),
        _blankspace: $ => token(/[\u0020\u0009\u000a\u000b\u000c\u000d\u0085\u200e\u200f\u2028\u2029]/uy)
            },
        });
       
