package org.company.service;

import java.util.List;

import org.company.entity.ProducedItem;
import org.company.repository.ProducedItemRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

@Service
public class CompanyService {
	
	@Autowired
	private ProducedItemRepository repository;
	
	
	public ProducedItem produceItem(int value) {
	    ProducedItem item = new ProducedItem();
	    item.setValue(value);
	    item.setStatus("PRODUCED");
	    return repository.save(item);
	}
	
	public ProducedItem consumeItem() {
	    ProducedItem item = repository.findTopByOrderByIdDesc();
	    if(item != null) {
	        item.setStatus("CONSUMED");
	        repository.save(item);
	    }
	    return item;
	}
	public List<ProducedItem> getAllItems() {
        return repository.findAll();
    }
}
