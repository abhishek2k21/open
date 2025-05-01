package org.company.controller;

import org.company.entity.ProducedItem;
import org.company.service.CompanyService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/company")
public class CompanyController {
	
	@Autowired CompanyService service;
	
	@PostMapping("/produce")
	public ProducedItem produce(@RequestParam int value) {
	    return service.produceItem(value);
	}
	
	@GetMapping("/consume")
	public ProducedItem consume() {
	    return service.consumeItem();
	}



}
