
def entity_list_2_org_name_dict(entity_list):
    '''
    transform new entities to org_name_dict, which is used to build org name dictionary(with indices)
    :param entity_list:
    :return:
    '''
    org_name_dict = {}
    for entity in entity_list:
        if entity["is_org"]:
            org_name_dict[entity["name"]] = 0
            for org in entity["rel_org"]:
                org_name_dict[org] = 0
        else:
            pass
    return org_name_dict


def update_query_seed_dict_by_query_list(new_query_list, seed_dict):
    for query in new_query_list:
        if query not in seed_dict:
            seed_dict[query] = 0
    return seed_dict


def update_query_seed_dict_by_entity_list(entity_list, seed_dict):
    '''
    update query_seed_dict by new entities; seed dict should be keep only one
    :param entity_list:
    :param seed_dict:
    :return:
    '''
    for entity in entity_list:
        # mark query that has been got done
        query_done = entity["query_str"] if "query_str" in entity else None
        if query_done is not None and query_done in seed_dict:
            seed_dict[query_done] = 1

        # add new seed
        relevant_org_list = entity["rel_org"]
        for org in relevant_org_list:
            if org not in seed_dict:
                seed_dict[org] = 0

    return seed_dict