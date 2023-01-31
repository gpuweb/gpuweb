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
        global_directive: $ => $.enable_directive,
        global_decl: $ => choice(
            token(';'),
            seq($.global_variable_decl, token(';')),
            seq($.global_constant_decl, token(';')),
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
        literal: $ => choice(
            $.int_literal,
            $.float_literal,
            $.bool_literal
        ),
        member_ident: $ => $.ident_pattern_token,
        attribute: $ => choice(
            seq(token('@'), token('align'), token('('), $.expression, $.attrib_end),
            seq(token('@'), token('binding'), token('('), $.expression, $.attrib_end),
            seq(token('@'), token('builtin'), token('('), $.builtin_value_name, $.attrib_end),
            seq(token('@'), token('const')),
            seq(token('@'), token('group'), token('('), $.expression, $.attrib_end),
            seq(token('@'), token('id'), token('('), $.expression, $.attrib_end),
            seq(token('@'), token('interpolate'), token('('), $.interpolation_type_name, $.attrib_end),
            seq(token('@'), token('interpolate'), token('('), $.interpolation_type_name, token(','), $.interpolation_sample_name, $.attrib_end),
            seq(token('@'), token('invariant')),
            seq(token('@'), token('location'), token('('), $.expression, $.attrib_end),
            seq(token('@'), token('size'), token('('), $.expression, $.attrib_end),
            seq(token('@'), token('workgroup_size'), token('('), $.expression, $.attrib_end),
            seq(token('@'), token('workgroup_size'), token('('), $.expression, token(','), $.expression, $.attrib_end),
            seq(token('@'), token('workgroup_size'), token('('), $.expression, token(','), $.expression, token(','), $.expression, $.attrib_end),
            seq(token('@'), token('vertex')),
            seq(token('@'), token('fragment')),
            seq(token('@'), token('compute'))
        ),
        attrib_end: $ => seq(optional(token(',')), token(')')),
        array_type_specifier: $ => seq(token('array'), token('<'), $.type_specifier, optional(seq(token(','), $.element_count_expression)), token('>')),
        element_count_expression: $ => choice(
            $.additive_expression,
            $.bitwise_expression
        ),
        struct_decl: $ => seq(token('struct'), $.ident, $.struct_body_decl),
        struct_body_decl: $ => seq(token('{'), $.struct_member, optional(repeat1(seq(token(','), $.struct_member))), optional(token(',')), token('}')),
        struct_member: $ => seq(optional(repeat1($.attribute)), $.member_ident, token(':'), $.type_specifier),
        texture_and_sampler_types: $ => choice(
            $.sampler_type,
            $.depth_texture_type,
            seq($.sampled_texture_type, token('<'), $.type_specifier, token('>')),
            seq($.multisampled_texture_type, token('<'), $.type_specifier, token('>')),
            seq($.storage_texture_type, token('<'), $.texel_format, token(','), $.access_mode, token('>'))
        ),
        sampler_type: $ => choice(
            token('sampler'),
            token('sampler_comparison')
        ),
        sampled_texture_type: $ => choice(
            token('texture_1d'),
            token('texture_2d'),
            token('texture_2d_array'),
            token('texture_3d'),
            token('texture_cube'),
            token('texture_cube_array')
        ),
        multisampled_texture_type: $ => token('texture_multisampled_2d'),
        storage_texture_type: $ => choice(
            token('texture_storage_1d'),
            token('texture_storage_2d'),
            token('texture_storage_2d_array'),
            token('texture_storage_3d')
        ),
        depth_texture_type: $ => choice(
            token('texture_depth_2d'),
            token('texture_depth_2d_array'),
            token('texture_depth_cube'),
            token('texture_depth_cube_array'),
            token('texture_depth_multisampled_2d')
        ),
        type_alias_decl: $ => seq(token('alias'), $.ident, token('='), $.type_specifier),
        type_specifier: $ => choice(
            $.ident,
            $.type_specifier_without_ident
        ),
        type_specifier_without_ident: $ => choice(
            token('bool'),
            token('f32'),
            token('f16'),
            token('i32'),
            token('u32'),
            seq($.vec_prefix, token('<'), $.type_specifier, token('>')),
            seq($.mat_prefix, token('<'), $.type_specifier, token('>')),
            seq(token('ptr'), token('<'), $.address_space, token(','), $.type_specifier, optional(seq(token(','), $.access_mode)), token('>')),
            $.array_type_specifier,
            seq(token('atomic'), token('<'), $.type_specifier, token('>')),
            $.texture_and_sampler_types
        ),
        vec_prefix: $ => choice(
            token('vec2'),
            token('vec3'),
            token('vec4')
        ),
        mat_prefix: $ => choice(
            token('mat2x2'),
            token('mat2x3'),
            token('mat2x4'),
            token('mat3x2'),
            token('mat3x3'),
            token('mat3x4'),
            token('mat4x2'),
            token('mat4x3'),
            token('mat4x4')
        ),
        variable_statement: $ => choice(
            $.variable_decl,
            seq($.variable_decl, token('='), $.expression),
            seq(token('let'), $.optionally_typed_ident, token('='), $.expression),
            seq(token('const'), $.optionally_typed_ident, token('='), $.expression)
        ),
        variable_decl: $ => seq(token('var'), optional($.variable_qualifier), $.optionally_typed_ident),
        optionally_typed_ident: $ => seq($.ident, optional(seq(token(':'), $.type_specifier))),
        variable_qualifier: $ => seq(token('<'), $.address_space, optional(seq(token(','), $.access_mode)), token('>')),
        global_variable_decl: $ => seq(optional(repeat1($.attribute)), $.variable_decl, optional(seq(token('='), $.expression))),
        global_constant_decl: $ => choice(
            seq(token('const'), $.optionally_typed_ident, token('='), $.expression),
            seq(optional(repeat1($.attribute)), token('override'), $.optionally_typed_ident, optional(seq(token('='), $.expression)))
        ),
        primary_expression: $ => choice(
            $.ident,
            $.call_expression,
            $.literal,
            $.paren_expression,
            seq(token('bitcast'), token('<'), $.type_specifier, token('>'), $.paren_expression)
        ),
        call_expression: $ => $.call_phrase,
        call_phrase: $ => seq($.callable, $.argument_expression_list),
        callable: $ => choice(
            $.ident,
            $.type_specifier_without_ident,
            $.vec_prefix,
            $.mat_prefix,
            token('array')
        ),
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
            $.ident,
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
            seq($.unary_expression, token('<<'), $.unary_expression),
            seq($.unary_expression, token('>>'), $.unary_expression)
        ),
        relational_expression: $ => choice(
            $.shift_expression,
            seq($.shift_expression, token('<'), $.shift_expression),
            seq($.shift_expression, token('>'), $.shift_expression),
            seq($.shift_expression, token('<='), $.shift_expression),
            seq($.shift_expression, token('>='), $.shift_expression),
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
        compound_statement: $ => seq(token('{'), optional(repeat1($.statement)), token('}')),
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
            token('>>='),
            token('<<=')
        ),
        increment_statement: $ => seq($.lhs_expression, token('++')),
        decrement_statement: $ => seq($.lhs_expression, token('--')),
        if_statement: $ => seq($.if_clause, optional(repeat1($.else_if_clause)), optional($.else_clause)),
        if_clause: $ => seq(token('if'), $.expression, $.compound_statement),
        else_if_clause: $ => seq(token('else'), token('if'), $.expression, $.compound_statement),
        else_clause: $ => seq(token('else'), $.compound_statement),
        switch_statement: $ => seq(token('switch'), $.expression, token('{'), repeat1($.switch_body), token('}')),
        switch_body: $ => choice(
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
        loop_statement: $ => seq(token('loop'), token('{'), optional(repeat1($.statement)), optional($.continuing_statement), token('}')),
        for_statement: $ => seq(token('for'), token('('), $.for_header, token(')'), $.compound_statement),
        for_header: $ => seq(optional($.for_init), token(';'), optional($.expression), token(';'), optional($.for_update)),
        for_init: $ => choice(
            $.variable_statement,
            $.variable_updating_statement,
            $.func_call_statement
        ),
        for_update: $ => choice(
            $.variable_updating_statement,
            $.func_call_statement
        ),
        while_statement: $ => seq(token('while'), $.expression, $.compound_statement),
        break_statement: $ => token('break'),
        break_if_statement: $ => seq(token('break'), token('if'), $.expression, token(';')),
        continue_statement: $ => token('continue'),
        continuing_statement: $ => seq(token('continuing'), $.continuing_compound_statement),
        continuing_compound_statement: $ => seq(token('{'), optional(repeat1($.statement)), optional($.break_if_statement), token('}')),
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
            seq($.variable_statement, token(';')),
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
        function_header: $ => seq(token('fn'), $.ident, token('('), optional($.param_list), token(')'), optional(seq(token('->'), optional(repeat1($.attribute)), $.type_specifier))),
        param_list: $ => seq($.param, optional(repeat1(seq(token(','), $.param))), optional(token(','))),
        param: $ => seq(optional(repeat1($.attribute)), $.ident, token(':'), $.type_specifier),
        enable_directive: $ => seq(token('enable'), $.extension_name, token(';')),
        ident_pattern_token: $ => token(/([_\p{XID_Start}][\p{XID_Continue}]+)|([\p{XID_Start}])/uy),
        interpolation_type_name: $ => choice(
            token('perspective'),
            token('linear'),
            token('flat')
        ),
        interpolation_sample_name: $ => choice(
            token('center'),
            token('centroid'),
            token('sample')
        ),
        builtin_value_name: $ => choice(
            token('vertex_index'),
            token('instance_index'),
            token('position'),
            token('front_facing'),
            token('frag_depth'),
            token('local_invocation_id'),
            token('local_invocation_index'),
            token('global_invocation_id'),
            token('workgroup_id'),
            token('num_workgroups'),
            token('sample_index'),
            token('sample_mask')
        ),
        access_mode: $ => choice(
            token('read'),
            token('write'),
            token('read_write')
        ),
        address_space: $ => choice(
            token('function'),
            token('private'),
            token('workgroup'),
            token('uniform'),
            token('storage')
        ),
        texel_format: $ => choice(
            token('rgba8unorm'),
            token('rgba8snorm'),
            token('rgba8uint'),
            token('rgba8sint'),
            token('rgba16uint'),
            token('rgba16sint'),
            token('rgba16float'),
            token('r32uint'),
            token('r32sint'),
            token('r32float'),
            token('rg32uint'),
            token('rg32sint'),
            token('rg32float'),
            token('rgba32uint'),
            token('rgba32sint'),
            token('rgba32float'),
            token('bgra8unorm')
        ),
        extension_name: $ => token('f16'),
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
            token('CompileShader'),
            token('ComputeShader'),
            token('DomainShader'),
            token('GeometryShader'),
            token('Hullshader'),
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
            token('bf16'),
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
            token('f64'),
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
            token('handle'),
            token('highp'),
            token('i16'),
            token('i64'),
            token('i8'),
            token('impl'),
            token('implements'),
            token('import'),
            token('inline'),
            token('inout'),
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
            token('quat'),
            token('readonly'),
            token('ref'),
            token('regardless'),
            token('register'),
            token('reinterpret_cast'),
            token('requires'),
            token('resource'),
            token('restrict'),
            token('self'),
            token('set'),
            token('shared'),
            token('signed'),
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
            token('u16'),
            token('u64'),
            token('u8'),
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
        ident: $ => $.ident_pattern_token,
        _comment: $ => token('//.*'),
        _blankspace: $ => token(/[\u0020\u0009\u000a\u000b\u000c\u000d\u0085\u200e\u200f\u2028\u2029]/uy)
    },
});
